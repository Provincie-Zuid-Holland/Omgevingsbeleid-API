from typing import Optional

from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder


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
