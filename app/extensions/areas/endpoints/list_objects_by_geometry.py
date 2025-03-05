import uuid
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from shapely import wkt

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_sorted_pagination_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import OrderConfig, PagedResponse, PaginatedQueryResult, SortedPagination
from app.extensions.areas.dependencies import depends_area_geometry_repository, depends_area_repository
from app.extensions.areas.models.models import VALID_GEOMETRIES, GeometryFunctions, GeoSearchResult
from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository
from app.extensions.areas.repository.area_repository import AreaRepository


class ListObjectsByGeometryRequestData(BaseModel):
    Object_Types: List[str] = Field(default_factory=list)
    Geometry: str
    Function: GeometryFunctions = Field(GeometryFunctions.INTERSECTS)

    @field_validator("Geometry")
    def valid_area_list(cls, v):
        try:
            geom = wkt.loads(v)
            if geom.geom_type in VALID_GEOMETRIES:
                return v

            raise ValueError("Geometry is not a valid shape")
        except Exception as e:
            raise ValueError("Geometry is not a valid shape")


class ListObjectsByGeometryEndpoint(Endpoint):
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
            object_in: ListObjectsByGeometryRequestData,
            pagination: SortedPagination = Depends(depends_sorted_pagination_curried(self._order_config)),
            geometry_repository: AreaGeometryRepository = Depends(depends_area_geometry_repository),
            area_repository: AreaRepository = Depends(depends_area_repository),
        ) -> PagedResponse[GeoSearchResult]:
            return self._handler(
                geometry_repository=geometry_repository,
                area_repository=area_repository,
                pagination=pagination,
                object_in=object_in,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PagedResponse[GeoSearchResult],
            summary=f"List the objects in werkingsgebieden by a geometry",
            description=None,
            tags=["Areas"],
        )

        return router

    def _handler(
        self,
        geometry_repository: AreaGeometryRepository,
        area_repository: AreaRepository,
        pagination: SortedPagination,
        object_in: ListObjectsByGeometryRequestData,
    ) -> PagedResponse[GeoSearchResult]:
        self._guard(object_in)

        area_uuids: List[uuid.UUID] = geometry_repository.get_area_uuids_by_geometry(
            geometry=object_in.Geometry,
            geometry_func=object_in.Function,
        )
        paginated_result: PaginatedQueryResult = area_repository.get_latest_by_areas(
            area_object_type=self._area_object_type,
            areas=area_uuids,
            object_types=object_in.Object_Types,
            pagination=pagination,
        )
        object_list = [
            GeoSearchResult(
                UUID=item.UUID,
                Area_UUID=item.Area_UUID,
                Object_Type=item.Object_Type,
                Titel=item.Title,
                Omschrijving=item.Description,
            )
            for item in paginated_result.items
        ]

        return PagedResponse(
            total=paginated_result.total_count,
            limit=pagination.limit,
            offset=pagination.offset,
            results=object_list,
        )

    def _guard(self, object_in: ListObjectsByGeometryRequestData):
        for obj_type in object_in.Object_Types:
            if obj_type not in self._allowed_result_object_types:
                raise ValueError(f"object types allowed: {str(self._allowed_result_object_types)}")


class ListObjectsByGeometryEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "areas_list_objects_by_geometry"

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

        return ListObjectsByGeometryEndpoint(
            path=path,
            area_object_type=area_object_type,
            allowed_result_object_types=allowed_result_object_types,
            order_config=order_config,
        )
