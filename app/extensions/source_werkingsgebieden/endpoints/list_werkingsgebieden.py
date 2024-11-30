from typing import List, Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SimplePagination
from app.extensions.source_werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.source_werkingsgebieden.models.models import Werkingsgebied
from app.extensions.source_werkingsgebieden.repository.mssql_geometry_repository import GeometryRepository
from app.extensions.source_werkingsgebieden.repository.mssql_geometry_repository import MssqlGeometryRepository


class ListWerkingsgebiedenEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: SimplePagination = Depends(depends_simple_pagination),
            repository: GeometryRepository = Depends(depends_geometry_repository),
            title: Optional[str] = None,
        ) -> PagedResponse[Werkingsgebied]:
            return self._handler(repository, pagination, title)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[Werkingsgebied],
            summary=f"List the werkingsgebieden",
            description=None,
            tags=["Source Werkingsgebieden"],
        )

        return router

    def _handler(
        self, repository: GeometryRepository, pagination: SimplePagination, title: Optional[str] = None
    ) -> PagedResponse[Werkingsgebied]:
        if title is None:
            total_count, werkingsgebieden_dicts = repository.get_werkingsgebieden_grouped_by_title(pagination)
        else:
            total_count, werkingsgebieden_dicts = repository.get_werkingsgebieden_hashed(pagination, title)

        werkingsgebieden: List[Werkingsgebied] = []
        for row in werkingsgebieden_dicts:
            werkingsgebied = Werkingsgebied(**row)
            werkingsgebieden.append(werkingsgebied)

        return PagedResponse[Werkingsgebied](
            total=total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=werkingsgebieden,
        )


class ListWerkingsgebiedenEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "source_list_werkingsgebieden"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        return ListWerkingsgebiedenEndpoint(
            path=path,
            order_config=order_config,
        )
