from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user
from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable
from app.extensions.werkingsgebieden.dependencies import (
    depends_werkingsgebieden_repository,
)
from app.extensions.werkingsgebieden.models.models import Werkingsgebied
from app.extensions.werkingsgebieden.repository.werkingsgebieden_repository import (
    WerkingsgebiedenRepository,
)


class ListWerkingsgebiedenEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            repository: WerkingsgebiedenRepository = Depends(
                depends_werkingsgebieden_repository
            ),
        ) -> List[Werkingsgebied]:
            return self._handler(repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[Werkingsgebied],
            summary=f"List the werkingsgebieden",
            description=None,
            tags=["Werkingsgebieden"],
        )

        return router

    def _handler(
        self,
        repository: WerkingsgebiedenRepository,
    ) -> List[Werkingsgebied]:
        table_werkingsgebieden: List[WerkingsgebiedenTable] = repository.get_all()
        werkingsgebieden: List[Werkingsgebied] = [
            Werkingsgebied.from_orm(w) for w in table_werkingsgebieden
        ]

        return werkingsgebieden


class ListWerkingsgebiedenEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_werkingsgebieden"

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

        return ListWerkingsgebiedenEndpoint(
            path=path,
        )
