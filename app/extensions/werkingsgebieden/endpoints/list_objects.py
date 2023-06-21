from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, conlist

from app.dynamic.dependencies import depends_pagination
from app.dynamic.utils import pagination

from app.dynamic.utils.pagination import Pagination
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, query_paginated
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user
from app.extensions.werkingsgebieden.dependencies import (
    depends_werkingsgebieden_repository,
)
from app.extensions.werkingsgebieden.models.models import (
    GeoSearchResult,
    SearchResultWrapper,
)
from app.extensions.werkingsgebieden.repository.werkingsgebieden_repository import (
    WerkingsgebiedenRepository,
)


class AreaListSchema(BaseModel):
    # sensible max value?
    Area_List = conlist(UUID, min_items=1, max_items=300)


class ListObjectsInGeoEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: AreaListSchema,
            pagination: Pagination = Depends(depends_pagination),
            user: UsersTable = Depends(depends_current_active_user),
            repository: WerkingsgebiedenRepository = Depends(
                depends_werkingsgebieden_repository
            ),
        ) -> PagedResponse[GeoSearchResult]:
            return self._handler(
                repository=repository,
                area_list=object_in.Area_List,
                offset=pagination.get_offset(),
                limit=pagination.get_limit(),
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary=f"List the objects active in werkingsgebieden",
            description=None,
            tags=["Search"],
        )

        return router

    def _handler(
        self,
        repository: WerkingsgebiedenRepository,
        area_list: List[UUID],
        offset: int,
        limit: int,
    ):
        return repository.get_latest_in_area(
            in_area=area_list, limit=limit, offset=offset
        )


class ListObjectsInGeoEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_objects_in_werkingsgebieden"

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

        return ListObjectsInGeoEndpoint(
            path=path,
        )
