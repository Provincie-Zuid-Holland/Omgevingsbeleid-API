from typing import Annotated, Generator, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder
from app.core.db.session import SessionFactoryType, session_scope


@inject
def depends_db_session(
    session_factory: Annotated[SessionFactoryType, Depends(Provide[ApiContainer.db_session_factory])],
) -> Generator[Session, None]:
    with session_scope(session_factory) as session:
        yield session


def depends_simple_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> SimplePagination:
    return SimplePagination(offset=offset, limit=limit)


def depends_optional_sorted_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[SortOrder] = None,
) -> OptionalSortedPagination:
    optional_sort = OptionalSort(
        column=sort_column,
        order=sort_order,
    )
    pagination = OptionalSortedPagination(
        offset=offset,
        limit=limit,
        sort=optional_sort,
    )
    return pagination
