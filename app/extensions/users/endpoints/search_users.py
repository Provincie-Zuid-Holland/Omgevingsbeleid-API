from typing import List, Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_user_repository
from app.extensions.users.model import User
from app.extensions.users.repository.user_repository import UserRepository


class SearchUsersEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            role: Optional[str] = None,
            query: Optional[str] = None,
            active: Optional[bool] = None,
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            user: UsersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> PagedResponse[User]:
            return self._handler(user_repository, pagination, role, query, active)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[User],
            summary=f"Search the users",
            description=None,
            tags=["User"],
        )

        return router

    def _handler(
        self,
        repostiory: UserRepository,
        pagination: SortedPagination,
        role: Optional[str],
        query: Optional[str],
        active: Optional[bool],
    ) -> PagedResponse[User]:
        paginated_result = repostiory.get_filtered(pagination, role, query, active)
        users: List[User] = [User.model_validate(u) for u in paginated_result.items]

        return PagedResponse[User](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=users,
        )


class SearchUsersEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "search_users"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return SearchUsersEndpoint(
            path=path,
            order_config=order_config,
        )
