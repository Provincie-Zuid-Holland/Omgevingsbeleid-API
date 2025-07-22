from typing import Annotated, Optional
import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.werkingsgebieden.repositories.input_geo_werkingsgebieden_repository import (
    InputGeoWerkingsgebiedenRepository,
)
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebiedenSortColumn
from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SortOrder
from sqlalchemy.orm import Session

from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable


def depends_optional_input_geo_werkingsgebieden_sorted_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort_column: Optional[InputGeoWerkingsgebiedenSortColumn] = None,
    sort_order: Optional[SortOrder] = None,
) -> OptionalSortedPagination:
    optional_sort = OptionalSort(
        column=sort_column.value if sort_column else None,
        order=sort_order,
    )
    pagination = OptionalSortedPagination(
        offset=offset,
        limit=limit,
        sort=optional_sort,
    )
    return pagination


@inject
def depends_input_geo_werkingsgebied(
    input_geo_werkingsgebied_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        InputGeoWerkingsgebiedenRepository, Depends(Provide[ApiContainer.input_geo_werkingsgebieden_repository])
    ],
) -> InputGeoWerkingsgebiedenTable:
    maybe_werkingsgebied: Optional[InputGeoWerkingsgebiedenTable] = repository.get_by_id(
        session, input_geo_werkingsgebied_uuid
    )
    if not maybe_werkingsgebied:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Input Geo Werkingsgebied niet gevonden")
    return maybe_werkingsgebied
