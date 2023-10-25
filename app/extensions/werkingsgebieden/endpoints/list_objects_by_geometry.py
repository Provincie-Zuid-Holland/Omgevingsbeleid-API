from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, validator
from shapely import wkt

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, PaginatedQueryResult, SortedPagination
from app.extensions.werkingsgebieden.dependencies import depends_werkingsgebieden_repository
from app.extensions.werkingsgebieden.models.models import VALID_GEOMETRIES, GeometryFunctions, GeoSearchResult
from app.extensions.werkingsgebieden.repository.werkingsgebieden_repository import WerkingsgebiedenRepository


class ListObjectsByGeometryRequestData(BaseModel):
    Geometry: str
    Function: GeometryFunctions = Field(GeometryFunctions.OVERLAPS)
    Object_Types: List[str] = Field([])

    @validator("Geometry")
    def valid_area_list(cls, v):
        try:
            geom = wkt.loads(v)
            if geom.geom_type in VALID_GEOMETRIES:
                return v

            raise ValueError("Geometry is not a valid shape")
        except Exception as e:
            raise ValueError("Geometry is not a valid shape")


class ListObjectsByGeometryEndpoint(Endpoint):
    def __init__(self, path: str, order_config: OrderConfig, allowed_object_types: List[str]):
        self._path: str = path
        self._order_config: OrderConfig = order_config
        self._allowed_object_types: List[str] = allowed_object_types

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ListObjectsByGeometryRequestData,
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            repository: WerkingsgebiedenRepository = Depends(depends_werkingsgebieden_repository),
        ) -> PagedResponse[GeoSearchResult]:
            return self._handler(
                repository=repository,
                pagination=pagination,
                object_in=object_in,
                order_config=self._order_config,
                allowed_object_types=self._allowed_object_types,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary=f"List the objects in werkingsgebieden by a geometry",
            description=None,
            tags=["Search"],
        )

        return router

    def _handler(
        self,
        repository: WerkingsgebiedenRepository,
        pagination: SortedPagination,
        object_in: ListObjectsByGeometryRequestData,
        order_config: OrderConfig,
        allowed_object_types: List[str],
    ) -> PagedResponse[GeoSearchResult]:
        object_types: List[str] = object_in.Object_Types or allowed_object_types
        for object_type in object_types:
            if object_type not in allowed_object_types:
                raise ValueError(f"Allowed Object_Types are: {allowed_object_types}")

        paginated_result: PaginatedQueryResult = repository.get_latest_by_geometry(
            geometry=object_in.Geometry,
            function=object_in.Function,
            object_types=object_types,
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


class ListObjectsByGeometryEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_objects_by_geometry"

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

        allowed_object_types: List[str] = resolver_config.get("allowed_object_types", [])
        if not allowed_object_types:
            raise RuntimeError("Missing required config allowed_object_types")

        return ListObjectsByGeometryEndpoint(
            path=path,
            order_config=order_config,
            allowed_object_types=allowed_object_types,
        )
