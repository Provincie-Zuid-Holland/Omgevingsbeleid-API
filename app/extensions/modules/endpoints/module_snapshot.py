from typing import List

from fastapi import APIRouter, Depends
from app.core.utils.utils import table_to_dict

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_module,
    depends_module_object_repository,
    depends_module_status_by_id,
)
from app.extensions.modules.models.models import ModuleSnapshot
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        module_object_repository: ModuleObjectRepository,
        user: UsersTable,
        module: ModuleTable,
        status: ModuleStatusHistoryTable,
    ):
        self._module_object_repository: ModuleObjectRepository = (
            module_object_repository
        )
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._status: ModuleStatusHistoryTable = status

    def handle(self) -> ModuleSnapshot:
        module_objects: List[
            ModuleObjectsTable
        ] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._status.Created_Date,
        )
        dict_objects: List[dict] = [table_to_dict(t) for t in module_objects]

        response: ModuleSnapshot = ModuleSnapshot(
            Objects=dict_objects,
        )
        return response


class ModuleSnapshotEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
    ):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_module),
            status: ModuleStatusHistoryTable = Depends(depends_module_status_by_id),
            module_object_repository: ModuleObjectRepository = Depends(
                depends_module_object_repository
            ),
        ) -> ModuleSnapshot:
            handler: EndpointHandler = EndpointHandler(
                module_object_repository,
                user,
                module,
                status,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=ModuleSnapshot,
            summary=f"Get snapshot of a module by status id",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleSnapshotEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_snapshot"

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

        return ModuleSnapshotEndpoint(
            path=path,
        )
