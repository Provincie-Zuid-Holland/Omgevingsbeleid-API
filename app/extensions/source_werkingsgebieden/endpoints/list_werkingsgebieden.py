from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, SortedPagination
from app.extensions.source_werkingsgebieden.dependencies import depends_werkingsgebieden_repository
from app.extensions.source_werkingsgebieden.models.models import Werkingsgebied
from app.extensions.source_werkingsgebieden.repository.werkingsgebieden_repository import WerkingsgebiedenRepository


class ListWerkingsgebiedenEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig):
        self._path: str = path
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            repository: WerkingsgebiedenRepository = Depends(depends_werkingsgebieden_repository),
        ) -> PagedResponse[Werkingsgebied]:
            return self._handler(repository, pagination)

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
        self, repository: WerkingsgebiedenRepository, pagination: SortedPagination
    ) -> PagedResponse[Werkingsgebied]:
        paged_results = repository.get_all_paginated(pagination)

        werkingsgebieden: List[Werkingsgebied] = [Werkingsgebied.from_orm(w) for w in paged_results.items]
        return PagedResponse[Werkingsgebied](
            total=paged_results.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=werkingsgebieden,
        )


class ListWerkingsgebiedenEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "source_list_werkingsgebieden"

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

        return ListWerkingsgebiedenEndpoint(
            path=path,
            order_config=order_config,
        )
