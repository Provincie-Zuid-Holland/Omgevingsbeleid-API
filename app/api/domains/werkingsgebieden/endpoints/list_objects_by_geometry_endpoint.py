import uuid
from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from shapely import wkt

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import (
    VALID_GEOMETRIES,
    AreaRepository,
    GeometryFunctions,
)
from app.api.domains.werkingsgebieden.types import GeoSearchResult
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import (
    OptionalSortedPagination,
    OrderConfig,
    PagedResponse,
    PaginatedQueryResult,
    Sort,
    SortedPagination,
)


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


class ListObjectByGeometryEndpointContext(BaseEndpointContext):
    area_object_type: str
    allowed_result_object_types: List[str]
    order_config: OrderConfig


@inject
def get_list_objects_by_geometry_endpoint(
    object_in: ListObjectsByGeometryRequestData,
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    geometry_repository: Annotated[AreaGeometryRepository, Depends(Provide[ApiContainer.area_geometry_repository])],
    area_repository: Annotated[AreaRepository, Depends(Provide[ApiContainer.area_repository])],
    context: Annotated[ListObjectByGeometryEndpointContext, Depends()],
) -> PagedResponse[GeoSearchResult]:
    for obj_type in object_in.Object_Types:
        if obj_type not in context.allowed_result_object_types:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, f"object types allowed: {str(context.allowed_result_object_types)}"
            )

    area_uuids: List[uuid.UUID] = geometry_repository.get_area_uuids_by_geometry(
        geometry=object_in.Geometry,
        geometry_func=object_in.Function,
    )

    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)
    paginated_result: PaginatedQueryResult = area_repository.get_latest_by_areas(
        area_object_type=context.area_object_type,
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
