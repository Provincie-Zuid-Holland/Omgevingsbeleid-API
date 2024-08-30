from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import FilterObjectCode, depends_filter_object_code
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, PaginatedQueryResult, SortOrder
from app.extensions.modules.dependencies import depends_module_repository, depends_module_sorted_pagination_curried
from app.extensions.modules.models import Module
from app.extensions.modules.repository.module_repository import (
    ModuleRepository,
    ModuleSortColumn,
    ModuleSortedPagination,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ListModulesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            only_mine: bool = False,
            filter_activated: Optional[bool] = None,
            filter_closed: Optional[bool] = None,
            filter_successful: Optional[bool] = None,
            filter_title: Optional[str] = None,
            pagination: ModuleSortedPagination = Depends(
                depends_module_sorted_pagination_curried(
                    ModuleSortColumn.Created_Date,
                    SortOrder.DESC,
                )
            ),
            user: UsersTable = Depends(depends_current_active_user),
            module_repository: ModuleRepository = Depends(depends_module_repository),
            object_code: Optional[FilterObjectCode] = Depends(depends_filter_object_code),
        ) -> PagedResponse[Module]:
            return self._handler(
                module_repository,
                user,
                only_mine,
                filter_activated,
                filter_closed,
                filter_successful,
                filter_title,
                object_code,
                pagination,
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
        filter_activated: Optional[bool],
        filter_closed: Optional[bool],
        filter_successful: Optional[bool],
        filter_title: Optional[str],
        object_code: Optional[FilterObjectCode],
        pagination: ModuleSortedPagination,
    ):
        filter_on_me: Optional[UUID] = None
        if only_mine is not None:
            filter_on_me = user.UUID

        paginated_result: PaginatedQueryResult = module_repository.get_with_filters(
            pagination=pagination,
            filter_activated=filter_activated,
            filter_closed=filter_closed,
            filter_successful=filter_successful,
            filter_title=filter_title,
            mine=filter_on_me,
            object_code=object_code,
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
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListModulesEndpoint(path)
