from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import (
    FilterObjectCode,
    depends_filter_object_code,
    depends_pagination,
)
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, Pagination
from app.extensions.modules.dependencies import depends_module_repository
from app.extensions.modules.models import Module
from app.extensions.modules.repository.module_repository import ModuleRepository
from app.extensions.users.db.tables import UsersTable
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
            pagination: Pagination = Depends(depends_pagination),
            user: UsersTable = Depends(depends_current_active_user),
            module_repository: ModuleRepository = Depends(depends_module_repository),
            object_code: Optional[FilterObjectCode] = Depends(
                depends_filter_object_code
            ),
        ) -> PagedResponse[Module]:
            return self._handler(
                module_repository, user, only_mine, only_active, object_code, pagination
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[Module],
            summary=f"List the modules",
            description=None,
            tags=["Modules"],
        )

        return router

    def _handler(
        self,
        module_repository: ModuleRepository,
        user: UsersTable,
        only_mine: bool,
        only_active: bool,
        object_code: Optional[FilterObjectCode],
        pagination: Pagination,
    ):
        filter_on_me: Optional[UUID] = None
        if only_mine:
            filter_on_me = user.UUID

        paginated_result = module_repository.get_with_filters(
            only_active=only_active,
            mine=filter_on_me,
            object_code=object_code,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        modules = [Module.from_orm(r) for r in paginated_result.items]

        return PagedResponse[Module](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=modules,
        )


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
