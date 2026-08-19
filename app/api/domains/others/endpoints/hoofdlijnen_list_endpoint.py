from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session, depends_optional_sorted_pagination
from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository, HoofdlijnSortColumn
from app.api.domains.others.types import Hoofdlijn
from app.api.domains.users.dependencies import depends_current_user
from app.api.utils.pagination import (
    OptionalSortedPagination,
    PagedResponse,
    PaginatedQueryResult,
    Sort,
    SortedPagination,
    SortOrder,
)
from app.core.tables.users import UsersTable


@inject
def get_hoofdlijnen_list_endpoint(
    _: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    hoofdlijn_repository: Annotated[HoofdlijnRepository, Depends(Provide[ApiContainer.hoofdlijn_repository])],
    optional_pagination: Annotated[OptionalSortedPagination, Depends(depends_optional_sorted_pagination)],
) -> PagedResponse[Hoofdlijn]:
    pagination: SortedPagination = optional_pagination.with_sort(
        Sort(
            column=HoofdlijnSortColumn.Created_Date,
            order=SortOrder.DESC,
        )
    )

    paginated_result: PaginatedQueryResult = hoofdlijn_repository.get_paginated(
        session=session,
        pagination=pagination,
    )

    # hoofdlijnen = [Hoofdlijn.model_validate(r) for r in paginated_result.items]
    hoofdlijnen = []
    for r in paginated_result.items:
        validated = Hoofdlijn.model_validate(r)
        hoofdlijnen.append(validated)

    return PagedResponse[Hoofdlijn](
        total=paginated_result.total_count,
        offset=pagination.offset,
        limit=pagination.limit,
        results=hoofdlijnen,
    )
