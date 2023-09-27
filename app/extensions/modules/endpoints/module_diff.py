from datetime import datetime
from enum import Enum
from typing import List, Optional
import subprocess

import diff_match_patch
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
        module: ModuleTable,
        status: Optional[ModuleStatusHistoryTable],
        output_format: Format,
    ):
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._object_repository: ObjectRepository = object_repository
        self._module: ModuleTable = module
        self._status: Optional[ModuleStatusHistoryTable] = status
        self._output_format: Format = output_format
        self._timepoint: datetime = self._status.Created_Date if self._status is not None else datetime.utcnow()

    def handle(self) -> FileResponse:
        module_objects: List[ModuleObjectsTable] = self._get_module_objects()
        # module_objects.sort(key=lambda mo: mo.Code)

        contents = []
        for module_object in module_objects:
            object_response = self._generate_for_module_object(module_object)
            if object_response:
                contents.append(object_response)

        html_content = '<br style="page-break-before: always">'.join(contents)
        as_response: FileResponse = self._format_response(html_content)
        return as_response

    def _format_response(self, html_content: str) -> FileResponse:
        html_path: str = self._generate_filename(Format.HTML)
        with open(html_path, 'w') as file:
            file.write(html_content)

        if self._output_format == Format.ODT:
            cmd = ['libreoffice', '--headless', '--convert-to', Format.ODT, html_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            odt_path: str = self._generate_filename(Format.ODT)
            return FileResponse(odt_path)

        elif self._output_format == Format.DOC:
            # Cant transform from html to doc, needs ODT as inbetween format
            cmd = ['libreoffice', '--headless', '--convert-to', Format.ODT, html_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            odt_path: str = self._generate_filename(Format.ODT)

            cmd = ['libreoffice', '--headless', '--convert-to', Format.DOC, odt_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            doc_path: str = self._generate_filename(Format.DOC)
            return FileResponse(doc_path)

        elif self._output_format == Format.DOCX:
            # Cant transform from html to doc, needs ODT as inbetween format
            cmd = ['libreoffice', '--headless', '--convert-to', Format.ODT, html_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            odt_path: str = self._generate_filename(Format.ODT)

            cmd = ['libreoffice', '--headless', '--convert-to', Format.DOCX, odt_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            docx_path: str = self._generate_filename(Format.DOCX)
            return FileResponse(
                docx_path,
                headers={
                    'Content-Disposition': 'attachment;',
                },
            )

        elif self._output_format == Format.PDF:
            cmd = ['libreoffice', '--headless', '--convert-to', Format.PDF, html_path, '--outdir', '/tmp']
            result = subprocess.run(cmd)
            if result.returncode != 0:
                raise HTTPException(500)
            pdf_path: str = self._generate_filename(Format.PDF)
            return FileResponse(pdf_path)

        else: # html
            return FileResponse(html_path)

    def _generate_filename(self, file_format: Format) -> str:
        return f"/tmp/module-{self._module.Module_ID}-at-{self._timepoint.strftime('%Y-%m-%d-%H%M%S')}.{file_format.value}"

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
            diffs = dmp.diff_main(module_object.Description or "", valid_object.Description or "")
            html_result = dmp.prettyHtml(diffs)
            response.append(html_result)

        # @todo: fix assets here (via event)

        return "".join(response)

    def _get_module_objects(self) -> List[ModuleObjectsTable]:
        module_objects: List[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._timepoint,
        )

        # It was actually a ScalarResult but we need a list for sorting
        # return module_objects.all()
        return module_objects


class ModuleDiffEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            output_format: Format = Format.HTML,
            # @todo: This should be here, but its easier to test without logging in
            # user: UsersTable = Depends(depends_current_active_user),
            status: Optional[ModuleStatusHistoryTable] = Depends(depends_maybe_module_status_by_id),
            module: ModuleTable = Depends(depends_active_module),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            object_repository: ObjectRepository = Depends(depends_object_repository),
        ) -> FileResponse:
            handler: EndpointHandler = EndpointHandler(
                module_object_repository,
                object_repository,
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
