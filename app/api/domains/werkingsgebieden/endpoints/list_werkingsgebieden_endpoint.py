from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends

from dependency_injector.wiring import Provide, inject
from app.api.api_container import ApiContainer
from app.api.dependencies import depends_optional_sorted_pagination
from app.api.domains.werkingsgebieden.repositories.werkingsgebieden_repository import WerkingsgebiedenRepository
from app.api.domains.werkingsgebieden.types import Werkingsgebied
from app.api.endpoint import BaseEndpointContext
from app.api.utils.pagination import OptionalSortedPagination, OrderConfig, PagedResponse, SortedPagination



class ListWerkingsgebiedenEndpointContext(BaseEndpointContext):
    order_config: OrderConfig

@inject
async def get_list_werkingsgebieden_endpoint(
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
    repository: Annotated[WerkingsgebiedenRepository, Depends(Provide[ApiContainer.werkingsgebieden_repository])],
    context: Annotated[ListWerkingsgebiedenEndpointContext, Depends()],
    title: Optional[str] = None,
) -> PagedResponse[Werkingsgebied]:
    pagination: SortedPagination = optional_pagination.with_sort(context.order_config)

    if title is None:
        paged_results = repository.get_unique_paginated(pagination)
    else:
        paged_results = repository.get_by_title_paginated(pagination, title)

    werkingsgebieden: List[Werkingsgebied] = [Werkingsgebied.model_validate(w) for w in paged_results.items]

    return PagedResponse[Werkingsgebied](
        total=paged_results.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=werkingsgebieden,
    )
