import base64
import difflib
import re
import subprocess
from datetime import datetime
from enum import Enum
from io import BytesIO
from os import path
from typing import List, Optional
from uuid import UUID

from bs4 import BeautifulSoup, NavigableString, Tag
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectsTable
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.dependencies import depends_asset_repository
from app.extensions.html_assets.repository.assets_repository import AssetRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_maybe_module_status_by_id,
    depends_module_object_repository,
)
from app.extensions.modules.models.models import ModuleObjectActionFilter
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class Format(str, Enum):
    HTML = "html"
    ODT = "odt"
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"


class DisplayObjectContent(BaseModel):
    column: str
    label: str


class DisplayObject(BaseModel):
    object_type: str
    content: List[DisplayObjectContent]


class ObjectMappings(BaseModel):
    display_objects: List[DisplayObject]

    def get(self, object_type: str) -> DisplayObject:
        for o in self.display_objects:
            if o.object_type == object_type:
                return o
        raise RuntimeError(f"Unknown object_type {object_type}")


class Formatter:
    def __init__(self, output_format: Format, module_id: int, timepoint: datetime):
        self._output_format: Format = output_format
        self._module_id: int = module_id
        self._timepoint: datetime = timepoint
        self._workdir: str = "/tmp"

    def _generate_filepath(self, format: Format) -> str:
        return f"/tmp/module-{self._module_id}-at-{self._timepoint.strftime('%Y-%m-%d-%H%M%S')}.{format.value}"

    def _convert(self, input_path: str, target_format: Format):
        cmd = ["libreoffice", "--headless", "--convert-to", target_format.value, input_path, "--outdir", self._workdir]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise HTTPException(500)
        return self._generate_filepath(target_format)

    def format_response(self, html_content: str) -> FileResponse:
        html_path = self._generate_filepath(Format.HTML)
        with open(html_path, "w") as file:
            file.write(html_content)

        format_conversion_paths = {
            Format.ODT: [Format.ODT],
            Format.DOC: [Format.ODT, Format.DOC],
            Format.DOCX: [Format.ODT, Format.DOCX],
            Format.PDF: [Format.PDF],
            Format.HTML: [],
        }

        latest_path = html_path
        for target_format in format_conversion_paths.get(self._output_format, []):
            latest_path = self._convert(latest_path, target_format)

        return FileResponse(
            latest_path, headers={"Content-Disposition": f"attachment; filename={path.basename(latest_path)}"}
        )


def thumbnail(base64_string):
    prefix, base64_data = base64_string.split(";base64,")
    file_format = prefix.split("/")[-1]  # Extract format (e.g., "png" from "data:image/png")

    decoded_img = base64.b64decode(base64_data)

    img = Image.open(BytesIO(decoded_img))
    img.thumbnail((700, 1100))

    buffered = BytesIO()
    img.save(buffered, format=file_format.upper())
    resized_base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return f"{prefix};base64,{resized_base64_data}"


def tokenize_html(html_text):
    soup = BeautifulSoup(str(html_text), "lxml")
    tokens = []

    def process_text(text):
        # Split by the specified delimiters while keeping the delimiter
        segments = re.split(r"(?<=[.:\t\n ])", text)
        tokens.extend([segment for segment in segments if segment.strip() or segment == " "])

    def process_node(node):
        if isinstance(node, Tag):
            # Start tag with its attributes
            start_tag = str(node).split(">")[0] + ">"
            tokens.append(start_tag)
            for child in node.children:
                process_node(child)
            # End tag, but only for tags that are not self-closing
            if not node.isSelfClosing:
                tokens.append(f"</{node.name}>")
        elif isinstance(node, NavigableString):
            process_text(node.string)

    for content in soup.contents:
        process_node(content)

    return tokens


class EndpointHandler:
    def __init__(
        self,
        object_mapping: ObjectMappings,
        module_object_repository: ModuleObjectRepository,
        object_repository: ObjectRepository,
        asset_repository: AssetRepository,
        module: ModuleTable,
        status: Optional[ModuleStatusHistoryTable],
        output_format: Format,
    ):
        self._object_mapping: ObjectMappings = object_mapping
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._object_repository: ObjectRepository = object_repository
        self._asset_repository: AssetRepository = asset_repository
        self._module: ModuleTable = module
        self._status: Optional[ModuleStatusHistoryTable] = status
        self._output_format: Format = output_format
        self._timepoint: datetime = self._status.Created_Date if self._status is not None else datetime.utcnow()

    def handle(self) -> FileResponse:
        module_objects: List[ModuleObjectsTable] = self._get_module_objects()
        module_objects.sort(key=lambda mo: mo.Code)

        contents = []
        for module_object in module_objects:
            object_response = self._generate_for_module_object(module_object)
            if object_response:
                contents.append(object_response)

        html_body = '<br style="page-break-before: always">'.join(contents)

        html_css = """
html, body, h1, h2, h3, h4, h5, h6, del, ins, p, li, td, th {
    font-family: 'Carlito', 'Calibri', sans-serif;
}
del, ins, p, li, td, th {
    font-size: 11pt;
}
h2 ins, h2 del {
    display: inline;
    font-size: 18pt;
}
"""
        html_content = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Module Export</title>
    <link href="https://fonts.googleapis.com/css2?family=Carlito:wght@400;700&display=swap" rel="stylesheet">
    <style>
        {html_css}
    </style>
</head>
<body>
    {html_body}
</body>"""

        as_response: FileResponse = self._format_response(html_content)
        as_response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"

        return as_response

    def _get_module_objects(self) -> List[ModuleObjectsTable]:
        module_objects: List[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._timepoint,
        )

        return module_objects.all()

    def _as_diff(self, old_html_content: str, new_html_content: str) -> str:
        old_html_content = tokenize_html(old_html_content)
        new_html_content = tokenize_html(new_html_content)

        d = difflib.Differ()
        diff = d.compare(old_html_content, new_html_content)
        diff_list = list(diff)
        result = []
        for d in diff_list:
            op, line = d[:2], d[2:]
            if op == "  ":
                result.append(line)
            elif op == "- ":
                result.append('<del style="background:#FBE4D5;"><s>%s</s></del>' % line)
            elif op == "+ ":
                result.append('<ins style="background:#E2EFD9;">%s</ins>' % line)
        html_result = "".join(result)
        soup = BeautifulSoup(html_result, "html.parser")
        html_result = str(soup)
        return html_result

    def _generate_for_module_object(self, module_object: ModuleObjectsTable) -> str:
        response = []
        valid_object: Optional[ObjectsTable] = self._object_repository.get_latest_valid_by_id(
            module_object.Object_Type,
            module_object.Object_ID,
        )

        display_object = self._object_mapping.get(module_object.Object_Type)

        title = module_object.Title
        if valid_object is not None:
            title = self._as_diff(
                f"{module_object.Object_Type}: {valid_object.Title}", f"{module_object.Object_Type}: {title}"
            )

        response.append(f"<h2>{title}</h2>")
        # response.append(f"<h3>Toelichting</h3>")
        # response.append(module_object.ModuleObjectContext.Explanation)
        # response.append(f"<h3>Conclusie</h3>")
        # response.append(module_object.ModuleObjectContext.Conclusion)
        response.append(f"<h3>Inhoud</h3>")

        # @todo: I'm not sure about the "" anymore
        if module_object.ModuleObjectContext.Action in ["", ModuleObjectActionFilter.Terminate]:
            # It could be that there is no valid object at the moment, because it has been terminated in parallel
            if valid_object is None:
                response.append(f'<del style="background:#FBE4D5;">[Already terminated]</del>')
            else:
                for object_config in display_object.content:
                    response.append(f"<h4>{object_config.label}</h4>")
                    response.append(
                        f'<del style="background:#FBE4D5;"><s>{getattr(valid_object, object_config.column)}</s></del>'
                    )
        elif valid_object is None:
            for object_config in display_object.content:
                response.append(f"<h4>{object_config.label}</h4>")
                response.append(
                    f'<ins style="background:#E2EFD9;">{getattr(module_object, object_config.column)}</ins>'
                )
        else:
            for object_config in display_object.content:
                old_html_content = getattr(valid_object, object_config.column) or ""
                new_html_content = getattr(module_object, object_config.column) or ""

                html_result = self._as_diff(old_html_content, new_html_content)

                response.append(f"<h4>{object_config.label}</h4>")
                response.append(html_result)

        html_content = "".join(response)

        soup = BeautifulSoup(html_content, "html.parser")
        for img in soup.find_all("img", src=re.compile("^\[ASSET")):
            try:
                asset_uuid = UUID(img["src"].split(":")[1][:-1])
            except ValueError:
                continue

            asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(asset_uuid)
            if not asset:
                continue

            thumb = thumbnail(asset.Content)
            img["src"] = thumb
            img["style"] = "display: block;"
        html_content = str(soup)

        return html_content

    def _format_response(self, html_content: str) -> FileResponse:
        formatter: Formatter = Formatter(
            self._output_format,
            self._module.Module_ID,
            self._timepoint,
        )
        response: FileResponse = formatter.format_response(html_content)
        return response


class ModuleDiffEndpoint(Endpoint):
    def __init__(self, path: str, object_mapping: ObjectMappings):
        self._path: str = path
        self._object_mapping: ObjectMappings = object_mapping

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            output_format: Format = Format.HTML,
            user: UsersTable = Depends(depends_current_active_user),
            status: Optional[ModuleStatusHistoryTable] = Depends(depends_maybe_module_status_by_id),
            module: ModuleTable = Depends(depends_active_module),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            object_repository: ObjectRepository = Depends(depends_object_repository),
            asset_repository: AssetRepository = Depends(depends_asset_repository),
        ) -> FileResponse:
            handler: EndpointHandler = EndpointHandler(
                self._object_mapping,
                module_object_repository,
                object_repository,
                asset_repository,
                module,
                status,
                output_format,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Get difference of module to Vigerend",
            description=None,
            tags=["Modules"],
            response_class=FileResponse,
        )

        return router


class ModuleDiffEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_diff"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")

        objects = resolver_config["objects"]
        display_objects = [DisplayObject(**obj) for obj in objects]
        object_mapping = ObjectMappings(display_objects=display_objects)

        return ModuleDiffEndpoint(path=path, object_mapping=object_mapping)
