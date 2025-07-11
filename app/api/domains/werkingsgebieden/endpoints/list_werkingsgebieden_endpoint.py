from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.werkingsgebieden.repositories.werkingsgebieden_repository import WerkingsgebiedenRepository
from app.api.domains.werkingsgebieden.types import Werkingsgebied
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, Sort, SortedPagination


class ListWerkingsgebiedenEndpointContext(BaseEndpointContext):
    order_config: OrderConfig


@inject
def get_list_werkingsgebieden_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[WerkingsgebiedenRepository, Depends(Provide[ApiContainer.werkingsgebieden_repository])],
    context: Annotated[ListWerkingsgebiedenEndpointContext, Depends()],
    title: Optional[str] = None,
) -> PagedResponse[Werkingsgebied]:
    sort: Sort = context.order_config.get_sort(optional_pagination.sort)
    pagination: SortedPagination = optional_pagination.with_sort(sort)

    if title is None:
        paged_results = repository.get_unique_paginated(session, pagination)
    else:
        paged_results = repository.get_by_title_paginated(session, pagination, title)

    werkingsgebieden: List[Werkingsgebied] = [Werkingsgebied.model_validate(w) for w in paged_results.items]

    return PagedResponse[Werkingsgebied](
        total=paged_results.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=werkingsgebieden,
    )
