from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_pagination, depends_pagination_with_config_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, Pagination
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_user_repository
from app.extensions.users.model import UserShort
from app.extensions.users.repository.user_repository import UserRepository


class ListUsersEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: Pagination = Depends(depends_pagination_with_config_curried(self._order_config)),
            user: UsersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> PagedResponse[UserShort]:
            return self._handler(user_repository, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[UserShort],
            summary=f"List the users",
            description=None,
            tags=["User"],
        )

        return router

    def _handler(
        self,
        repostiory: UserRepository,
        pagination: Pagination,
    ) -> PagedResponse[UserShort]:
        paginated_result = repostiory.get_active(pagination)
        users: List[UserShort] = [UserShort.from_orm(u) for u in paginated_result.items]

        return PagedResponse[UserShort](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=users,
        )


class ListUsersEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_users"

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
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ListUsersEndpoint(
            path=path,
            order_config=order_config,
        )
