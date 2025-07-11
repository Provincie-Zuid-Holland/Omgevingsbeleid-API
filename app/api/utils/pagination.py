from enum import Enum
from typing import Any, Generic, List, Optional, Sequence, Tuple, TypeVar

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class Sort(BaseModel):
    column: str
    order: SortOrder


class OptionalSort(BaseModel):
    """
    Represents an optional sorting configuration for pagination.

    This class is named `OptionalSort` instead of using `Optional[Sort]` because it is designed to be part of
    `OptionalSortedPagination`. The main purpose of `OptionalSort` is to allow the client to provide partial
    sorting information (or none at all), while deferring the responsibility of filling in missing data with
    sensible defaults to the endpoint. At the time of constructing this class, sensible defaults are not yet
    available, so the endpoint must convert an `OptionalSort` instance into a fully defined `Sort` instance
    with default values.
    """

    column: Optional[str] = None
    order: Optional[SortOrder] = None


class OrderConfig(BaseModel):
    default_column: str
    default_order: SortOrder
    allowed_columns: List[str]

    def get_sort(self, given_sort: OptionalSort) -> Sort:
        sort_column = self._validate_column(given_sort.column)
        sort_order = given_sort.order or self.default_order
        return Sort(column=sort_column, order=sort_order)

    def _validate_column(self, column: Optional[str]) -> str:
        if column is None:
            return self.default_column
        if column in self.allowed_columns:
            return column
        raise ValueError("Invalid sort column")

    @staticmethod
    def from_dict(data: dict) -> "OrderConfig":
        default_data: dict = data["default"]
        default_column: str = default_data["column"]

        default_order: SortOrder = SortOrder.ASC
        if "order" in default_data:
            default_order = SortOrder[default_data["order"].upper()]

        allowed_columns: List[str] = data.get("allowed_columns", [])

        return OrderConfig(
            default_column=default_column,
            default_order=default_order,
            allowed_columns=allowed_columns,
        )


class SimplePagination(BaseModel):
    offset: int = Field(0)
    limit: int = Field(20)

    @field_validator("offset", mode="before")
    def default_offset(cls, v):
        if v is None:
            return 0
        if v < 0:
            return 0
        return v

    @field_validator("limit", mode="before")
    def default_limit(cls, v):
        if v is None:
            return 20
        if v > 1000:
            return 20
        return v


class SortedPagination(SimplePagination):
    sort: Sort


class OptionalSortedPagination(SimplePagination):
    sort: OptionalSort

    def with_sort(self, sort: Sort) -> SortedPagination:
        return SortedPagination(
            offset=self.offset,
            limit=self.limit,
            sort=sort,
        )


T = TypeVar("T", bound=BaseModel)


class PagedResponse(BaseModel, Generic[T]):
    total: int
    offset: int = 0
    limit: int = -1
    results: List[T]


class PaginatedQueryResult(BaseModel):
    items: Sequence[Any] = Field(default_factory=list)
    total_count: int = Field(0)


def query_paginated(
    query: Select,
    session: Session,
    limit: int = -1,
    offset: int = 0,
    sort: Optional[Tuple] = None,
) -> PaginatedQueryResult:
    """
    Extend a query with pagination and wrap the query results
    in a generic response containing pagination meta data.

    if `sort` arg is not provided, make sure the query given
    already has a order_by clause.

    `sort` should be a tuple like (column, sort_direction)
    where `sort_direction` is either 'asc' or 'desc'
    and `column` is the sqlalch column object.
    """
    paginated: Select = add_pagination(query, limit, offset, sort)
    results: Sequence[Any] = session.execute(paginated).scalars().all()
    total_count: int = query_total_count(query, session)
    return PaginatedQueryResult(items=list(results), total_count=total_count)


def add_pagination(
    query: Select,
    limit: int = -1,
    offset: int = 0,
    sort: Optional[Tuple] = None,
) -> Select:
    if sort is not None:
        column, sort_direction = sort
        if sort_direction == SortOrder.DESC:
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))

    result: Select = query.limit(limit).offset(offset)
    return result


def query_total_count(query: Select, session: Session) -> int:
    count_stmt: Select = select(func.count()).select_from(query.alias())
    total_count: int = session.execute(count_stmt).scalar_one()
    return total_count
