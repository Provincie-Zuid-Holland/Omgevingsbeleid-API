from enum import Enum
from typing import Any, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"


class Sort(BaseModel):
    column: str
    order: SortOrder


class OrderConfig(BaseModel):
    default_column: str
    default_order: SortOrder
    allowed_columns: List[str]

    def get_sort(self, given_column: Optional[str], given_order: Optional[SortOrder]) -> Sort:
        sort_column: str = given_column if given_column in self.allowed_columns else self.default_column
        sort_order: SortOrder = given_order or self.default_order

        result = Sort(
            column=sort_column,
            order=sort_order,
        )
        return result

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


class Pagination(BaseModel):
    offset: int = Field(default=None)
    limit: int = Field(default=None)
    sort: Sort

    @validator("offset", pre=True, always=True)
    def default_offset(cls, v):
        if v is None:
            return 0
        if v < 0:
            return 0
        return v

    @validator("limit", pre=True, always=True)
    def default_limit(cls, v):
        if v is None:
            return 20
        if v > 500:
            return 20
        return v


T = TypeVar("T", bound=BaseModel)


class PagedResponse(GenericModel, Generic[T]):
    """
    Wrap any response schema and add pagination metadata.
    """

    total: int
    offset: int = 0
    limit: int = -1
    results: List[T]


class PaginatedQueryResult(BaseModel):
    items: List[Any] = Field(...)
    total_count: int = Field(0)


def query_paginated(
    query: Select,
    session: Session,
    limit: int = -1,
    offset: int = 0,
    sort: Optional[Tuple] = None,
):
    """
    Extend a query with pagination and wrap the query results
    in a generic response containing pagination meta data.

    if `sort` arg is not provided, make sure the query given
    already has a order_by clause.

    `sort` should be a tuple like (column, sort_direction)
    where `sort_direction` is either 'asc' or 'desc'
    and `column` is the sqlalch column object.
    """
    paginated = _add_pagination(query, limit, offset, sort)
    results = session.execute(paginated).scalars().all()
    total_count = _query_total_count(query, session)
    return PaginatedQueryResult(items=list(results), total_count=total_count)


def _add_pagination(
    query: Select,
    limit: int = -1,
    offset: int = 0,
    sort: Optional[Tuple] = None,
):
    """
    Add pagination splits and sorting to a base query
    """
    if sort is not None:
        column, sort_direction = sort
        if sort_direction == SortOrder.DESC:
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))

    paginated = query.limit(limit).offset(offset)
    return paginated


def _query_total_count(query: Select, session: Session):
    """
    Seperate query executed for getting the total count
    """
    count_stmt = select(func.count()).select_from(query.alias())
    total_count = session.execute(count_stmt).scalar_one()
    return total_count
