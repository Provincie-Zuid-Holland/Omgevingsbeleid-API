from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import depends_module_repository
from app.extensions.modules.models import Module
from app.extensions.modules.repository.module_repository import ModuleRepository
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


class ListModulesEndpoint(Endpoint):
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        path: str,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            only_mine: bool = True,
            only_active: bool = True,
            user: GebruikersTable = Depends(depends_current_active_user),
            module_repository: ModuleRepository = Depends(depends_module_repository),
        ) -> List[Module]:
            return self._handler(module_repository, user, only_mine, only_active)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[Module],
            summary=f"List the modules",
            description=None,
            tags=["Modules"],
        )

        return router

    def _handler(
        self,
        module_repository: ModuleRepository,
        user: GebruikersTable,
        only_mine: bool,
        only_active: bool,
    ) -> List[Module]:
        filter_on_me: Optional[UUID] = None
        if only_mine:
            filter_on_me = user.UUID

        modules: List[ModuleTable] = module_repository.get_with_filters(
            only_active, filter_on_me
        )

        return modules


class ListModulesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_modules"

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

        return ListModulesEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
