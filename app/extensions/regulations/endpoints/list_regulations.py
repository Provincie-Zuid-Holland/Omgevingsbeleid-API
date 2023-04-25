from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.regulations.db.tables import RegulationsTable
from app.extensions.regulations.dependencies import depends_regulations_repository
from app.extensions.regulations.models.models import Regulation
from app.extensions.regulations.repository.regulations_repository import (
    RegulationsRepository,
)


class ListRegulationsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            repository: RegulationsRepository = Depends(depends_regulations_repository),
        ) -> List[Regulation]:
            return self._handler(repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[Regulation],
            summary=f"Get all regulations",
            description=None,
            tags=["Regulations"],
        )

        return router

    def _handler(self, repository: RegulationsRepository):
        rows: List[RegulationsTable] = repository.get_all()

        response: List[Regulation] = [Regulation.from_orm(r) for r in rows]

        return response


class ListRegulationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_regulations"

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

        return ListRegulationsEndpoint(path=path)
