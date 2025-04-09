from typing import Annotated, Optional

from app.api.utils import FilterCombiner, Filters
from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder


def depends_string_filters(
    all_filters: Annotated[Optional[str], None],
    any_filters: Annotated[Optional[str], None],
) -> Filters:
    filters = Filters()
    if all_filters:
        filters.add_from_string(FilterCombiner.AND, all_filters)

    if any_filters:
        filters.add_from_string(FilterCombiner.OR, any_filters)

    return filters


def depends_simple_pagination(
    offset: Annotated[Optional[int], None],
    limit: Annotated[Optional[int], None],
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
