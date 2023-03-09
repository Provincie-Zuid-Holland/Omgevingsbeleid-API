from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_user_repository,
)
from app.extensions.users.model import UserShort
from app.extensions.users.repository.user_repository import UserRepository


class ListUsersEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: GebruikersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> List[UserShort]:
            return self._handler(user_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[UserShort],
            summary=f"List the users",
            description=None,
            tags=["User"],
        )

        return router

    def _handler(
        self,
        repostiory: UserRepository,
    ) -> List[UserShort]:
        users: List[GebruikersTable] = repostiory.get_active()
        response: List[UserShort] = [UserShort.from_orm(u) for u in users]

        return response


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

        return ListUsersEndpoint(
            path=path,
        )
