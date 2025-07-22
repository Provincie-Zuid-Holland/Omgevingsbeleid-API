from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.werkingsgebieden.dependencies import depends_optional_input_geo_werkingsgebieden_sorted_pagination
from app.api.domains.werkingsgebieden.repositories.input_geo_werkingsgebieden_repository import (
    InputGeoWerkingsgebiedenRepository,
)
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebied
from app.api.domains.werkingsgebieden.types import input_geo_werkingsgebieden_order_config
from app.api.utils.pagination import OptionalSortedPagination, PagedResponse, Sort, SortedPagination


@inject
def get_input_geo_list_latest_werkingsgebieden_endpoint(
    optional_pagination: Annotated[
        OptionalSortedPagination, Depends(depends_optional_input_geo_werkingsgebieden_sorted_pagination)
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        InputGeoWerkingsgebiedenRepository, Depends(Provide[ApiContainer.input_geo_werkingsgebieden_repository])
    ],
) -> PagedResponse[InputGeoWerkingsgebied]:
    sort: Sort = input_geo_werkingsgebieden_order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    paged_results = repository.get_unique_paginated(session, pagination)
    werkingsgebieden: List[InputGeoWerkingsgebied] = [
        InputGeoWerkingsgebied.model_validate(w) for w in paged_results.items
    ]

    return PagedResponse[InputGeoWerkingsgebied](
        total=paged_results.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=werkingsgebieden,
    )
