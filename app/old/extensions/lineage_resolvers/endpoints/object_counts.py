from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models.models import ObjectCount
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ObjectCountsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            object_repository: ObjectRepository = Depends(depends_object_repository),
        ):
            return self._handler(user, object_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ObjectCount],
            summary=f"List object types with counts for loggedin user",
            description=None,
            tags=["Search"],
        )

        return router

    def _handler(
        self,
        user: UsersTable,
        object_repo: ObjectRepository,
    ):
        rows: List[ObjectCount] = object_repo.get_valid_counts(user.UUID)

        return rows


class ObjectCountsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "object_counts"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ObjectCountsEndpoint(path=path)
