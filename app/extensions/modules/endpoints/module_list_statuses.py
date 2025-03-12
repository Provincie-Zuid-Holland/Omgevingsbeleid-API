from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import depends_module, depends_module_status_repository
from app.extensions.modules.models.models import ModuleStatus
from app.extensions.modules.repository.module_status_repository import ModuleStatusRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleListStatusesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_module),
            status_repository: ModuleStatusRepository = Depends(depends_module_status_repository),
        ) -> List[ModuleStatus]:
            return self._handler(status_repository, module)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ModuleStatus],
            summary=f"Get status history of the module",
            description=None,
            tags=["Modules"],
        )

        return router

    def _handler(self, status_repository: ModuleStatusRepository, module: ModuleTable) -> List[ModuleStatus]:
        statuses: List[ModuleStatusHistoryTable] = status_repository.get_all_by_module_id(module.Module_ID)

        response: List[ModuleStatus] = [ModuleStatus.model_validate(r) for r in statuses]
        return response


class ModuleListStatusesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_list_statuses"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")

        return ModuleListStatusesEndpoint(path=path)
