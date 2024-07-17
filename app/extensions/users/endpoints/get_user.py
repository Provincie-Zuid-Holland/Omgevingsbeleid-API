import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_user_repository
from app.extensions.users.model import User
from app.extensions.users.repository.user_repository import UserRepository


class GetUserEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user_uuid: uuid.UUID,
            _: UsersTable = Depends(depends_current_active_user),
            user_repository: UserRepository = Depends(depends_user_repository),
        ) -> User:
            return self._handler(user_repository, user_uuid)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=User,
            summary=f"Get a user",
            description=None,
            tags=["User"],
        )

        return router

    def _handler(self, repostiory: UserRepository, user_uuid: uuid.UUID) -> User:
        db_user: Optional[UsersTable] = repostiory.get_by_uuid(user_uuid)
        if not db_user:
            raise ValueError(f"User does not exist")

        user: User = User.from_orm(db_user)
        return user


class GetUserEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "get_user"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return GetUserEndpoint(path=path)
