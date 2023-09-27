from datetime import datetime
from typing import List, Optional

import diff_match_patch
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

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
        user: UsersTable,
        module: ModuleTable,
        status: Optional[ModuleStatusHistoryTable],
    ):
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._object_repository: ObjectRepository = object_repository
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._status: Optional[ModuleStatusHistoryTable] = status

    def handle(self) -> HTMLResponse:
        module_objects: List[ModuleObjectsTable] = self._get_module_objects()
        # module_objects.sort(key=lambda mo: mo.Code)

        all_responses = []
        for module_object in module_objects:
            object_response = self._generate_for_module_object(module_object)
            if object_response:
                all_responses.append(object_response)

        joined_response = '<br style="page-break-before: always">'.join(all_responses)
        return joined_response

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

        if module_object.ModuleObjectContext.Action == "":
            response.append(f'<del style="background:#ffe6e6;">{valid_object.Description}</del>')
        elif valid_object is None:
            response.append(f'<ins style="background:#e6ffe6;">{module_object.Description}</ins>')
        else:
            dmp = html_diff()
            diffs = dmp.diff_main(module_object.Description or "", valid_object.Description or "")
            html_result = dmp.prettyHtml(diffs)
            response.append(html_result)

        return "".join(response)

    def _get_module_objects(self) -> List[ModuleObjectsTable]:
        before: datetime = self._status.Created_Date if self._status is not None else datetime.utcnow()
        module_objects: List[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            before,
        )

        # @todo: need to handle assets

        return module_objects


class ModuleDiffEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            status: Optional[ModuleStatusHistoryTable] = Depends(depends_maybe_module_status_by_id),
            module: ModuleTable = Depends(depends_active_module),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            object_repository: ObjectRepository = Depends(depends_object_repository),
        ) -> HTMLResponse:
            handler: EndpointHandler = EndpointHandler(
                module_object_repository,
                object_repository,
                user,
                module,
                status,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            summary=f"Get difference of module to Vigerend",
            description=None,
            tags=["Modules"],
            response_class=HTMLResponse,
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
