from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder


async def depends_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db_sessionmaker = request.app.state.db_sessionmaker

    # Commits when the block exits, rolls back on an exception.
    async with db_sessionmaker.begin() as session:
        yield session


async def depends_simple_pagination(
    offset: int | None = None,
    limit: int | None = None,
) -> SimplePagination:
    return SimplePagination(offset=offset, limit=limit)


async def depends_optional_sorted_pagination(
    offset: int | None = None,
    limit: int | None = None,
    sort_column: str | None = None,
    sort_order: SortOrder | None = None,
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
