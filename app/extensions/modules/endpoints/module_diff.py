import difflib
import re
import subprocess
from datetime import datetime
from enum import Enum
from os import path
from typing import List, Optional
from uuid import UUID
import base64
from io import BytesIO
from PIL import Image

import diff_match_patch
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db.objects_table import ObjectsTable
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
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class Format(str, Enum):
    HTML = "html"
    ODT = "odt"
    DOC = "doc"
    DOCX = "docx"
    PDF = "pdf"


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
    prefix, base64_data = base64_string.split(';base64,')
    file_format = prefix.split('/')[-1]  # Extract format (e.g., "png" from "data:image/png")

    decoded_img = base64.b64decode(base64_data)

    img = Image.open(BytesIO(decoded_img))
    img.thumbnail((800, 600))

    buffered = BytesIO()
    img.save(buffered, format=file_format.upper())
    resized_base64_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return f"{prefix};base64,{resized_base64_data}"


class html_diff(diff_match_patch.diff_match_patch):
    def prettyHtml(self, diffs):
        """Convert a diff array into a pretty HTML report.

        Args:
          diffs: Array of diff tuples.

        Returns:
          HTML representation.
        """
        html = []
        for op, text in diffs:
            if op == self.DIFF_INSERT:
                html.append('<ins style="background:#e6ffe6;">%s</ins>' % text)
            elif op == self.DIFF_DELETE:
                html.append('<del style="background:#ffe6e6;">%s</del>' % text)
            elif op == self.DIFF_EQUAL:
                html.append("<span>%s</span>" % text)
        return "".join(html)


class EndpointHandler:
    def __init__(
        self,
        module_object_repository: ModuleObjectRepository,
        object_repository: ObjectRepository,
        asset_repository: AssetRepository,
        module: ModuleTable,
        status: Optional[ModuleStatusHistoryTable],
        output_format: Format,
    ):
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

        html_content = '<br style="page-break-before: always">'.join(contents)
        as_response: FileResponse = self._format_response(html_content)
        return as_response

    def _get_module_objects(self) -> List[ModuleObjectsTable]:
        module_objects: List[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._timepoint,
        )

        return module_objects.all()

    def _generate_for_module_object(self, module_object: ModuleObjectsTable) -> str:
        response = []
        valid_object: Optional[ObjectsTable] = self._object_repository.get_latest_valid_by_id(
            module_object.Object_Type,
            module_object.Object_ID,
        )

        response.append(f"<h2>{module_object.Title}</h2>")
        response.append(f"<p>Object Type: {module_object.Object_Type}</p>")
        response.append(f"<h3>Toelichting</h3>")
        response.append(module_object.ModuleObjectContext.Explanation)
        response.append(f"<h3>Conclusie</h3>")
        response.append(module_object.ModuleObjectContext.Conclusion)
        response.append(f"<h3>Inhoud</h3>")

        # @todo: object types, and there fields should be supplied via the .yml
        if module_object.ModuleObjectContext.Action == "":
            response.append(f'<del style="background:#ffe6e6;">{valid_object.Description}</del>')
        elif valid_object is None:
            response.append(f'<ins style="background:#e6ffe6;">{module_object.Description}</ins>')
        else:
            dmp = html_diff()
            old_html_content = valid_object.Description or ""
            try:
                soup = BeautifulSoup(old_html_content, "html.parser")
                old_html_content = soup.prettify()
            except:
                pass

            new_html_content = module_object.Description or ""
            try:
                soup = BeautifulSoup(new_html_content, "html.parser")
                new_html_content = soup.prettify()
            except:
                pass
            old_html_content = [l.strip() for l in old_html_content.splitlines()]
            new_html_content = [l.strip() for l in new_html_content.splitlines()]
            # diffs = dmp.diff_main(new_html_content, old_html_content)
            # html_result = dmp.prettyHtml(diffs)
            d = difflib.Differ()
            diff = d.compare(new_html_content, old_html_content)
            diff_list = list(diff)
            result = []
            for d in diff_list:
                op, line = d[:2], d[2:]
                if op == "  ":
                    result.append(line)
                elif op == "- ":
                    result.append('<del style="background:#ffe6e6;">%s</del>' % line)
                elif op == "+ ":
                    result.append('<ins style="background:#e6ffe6;">%s</ins>' % line)
            html_result = "".join(result)
            soup = BeautifulSoup(html_result, "html.parser")
            html_result = str(soup)
            response.append(html_result)

        html_content = "".join(response)

        # @todo: resolve modified assets (the <img> tag will have <ins> and <del> which should be resolved)

        # @todo: fix assets here (via event)
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
    def __init__(self, path: str):
        self._path: str = path

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

        return ModuleDiffEndpoint(path=path)
