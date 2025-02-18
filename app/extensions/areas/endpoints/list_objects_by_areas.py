from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, validator

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, PaginatedQueryResult, SortedPagination
from app.extensions.areas.dependencies import depends_area_repository
from app.extensions.areas.models.models import GeoSearchResult
from app.extensions.areas.repository.area_repository import AreaRepository


class SearchGeoRequestData(BaseModel):
    Object_Types: List[str] = Field(default_factory=list)
    Area_List: List[UUID]

    class Config:
        arbitrary_types_allowed = True

    @validator("Area_List")
    def valid_area_list(cls, v):
        if len(v) < 1:
            raise ValueError("area_list requires at least 1 uuid")
        if len(v) > 300:
            raise ValueError("area_list is too large, max 300 items")
        return v


class ListObjectsByAreasEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        order_config: OrderConfig,
        area_object_type: str,
        allowed_result_object_types: List[str],
    ):
        self._path: str = path
        self._area_object_type: str = area_object_type
        self._allowed_result_object_types: List[str] = allowed_result_object_types
        self._order_config: OrderConfig = order_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: SearchGeoRequestData,
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            repository: AreaRepository = Depends(depends_area_repository),
        ) -> PagedResponse[GeoSearchResult]:
            return self._handler(
                repository=repository,
                pagination=pagination,
                object_in=object_in,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary=f"List the objects in the given areas",
            description=None,
            tags=["Areas"],
        )

        return router

    def _handler(
        self,
        repository: AreaRepository,
        pagination: SortedPagination,
        object_in: SearchGeoRequestData,
    ) -> PagedResponse[GeoSearchResult]:
        self._guard(object_in)

        paginated_result: PaginatedQueryResult = repository.get_latest_by_areas(
            area_object_type=self._area_object_type,
            areas=object_in.Area_List,
            object_types=object_in.Object_Types,
            pagination=pagination,
        )
        object_list = []
        for item in paginated_result.items:
            search_result = GeoSearchResult(
                Gebied=str(item.Gebied_UUID),
                Titel=item.Title,
                Omschrijving=item.Description,
                Type=item.Object_Type,
                UUID=item.UUID,
            )
            object_list.append(search_result)

        return PagedResponse(
            total=paginated_result.total_count,
            limit=pagination.limit,
            offset=pagination.offset,
            results=object_list,
        )

    def _guard(self, object_in: SearchGeoRequestData):
        for obj_type in object_in.Object_Types:
            if obj_type not in self._allowed_result_object_types:
                raise ValueError(f"object types allowed: {str(self._allowed_result_object_types)}")


class ListObjectsByAreasEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "areas_list_objects_by_areas"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])
        area_object_type: str = resolver_config["area_object_type"]
        allowed_result_object_types: List[str] = resolver_config["allowed_result_object_types"]

        return ListObjectsByAreasEndpoint(
            path=path,
            area_object_type=area_object_type,
            allowed_result_object_types=allowed_result_object_types,
            order_config=order_config,
        )
