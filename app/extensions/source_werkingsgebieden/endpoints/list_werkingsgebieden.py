from typing import List, Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination
from app.extensions.source_werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.source_werkingsgebieden.models.models import Werkingsgebied
from app.extensions.source_werkingsgebieden.repository import GeometryRepository


class ListWerkingsgebiedenEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            repository: GeometryRepository = Depends(depends_geometry_repository),
            title: Optional[str] = None,
        ) -> PagedResponse[Werkingsgebied]:
            sort = pagination.sort
            return self._handler(repository, pagination, title, sort.column, sort.order)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[Werkingsgebied],
            summary="List the werkingsgebieden",
            description=None,
            tags=["Source Werkingsgebieden"],
        )

        return router

    def _handler(
        self,
        repository: GeometryRepository,
        pagination: SortedPagination,
        title: Optional[str] = None,
        order_column: str = "Modified_Date",
        order_direction: str = "DESC",
    ) -> PagedResponse[Werkingsgebied]:
        if title is None:
            total_count, werkingsgebieden_dicts = repository.get_werkingsgebieden_grouped_by_title(
                pagination, order_column, order_direction
            )
        else:
            total_count, werkingsgebieden_dicts = repository.get_werkingsgebieden_hashed(
                pagination, title, order_column, order_direction
            )

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
