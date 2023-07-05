from typing import Generic, List, Tuple, TypeVar, Optional, Any

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

from sqlalchemy import func, select, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


class Pagination(BaseModel):
    offset: Optional[int] = Field(default=None)
    limit: Optional[int] = Field(default=None)
    sort: str = Field(default="asc")

    @property
    def get_offset(self) -> int:
        if self.offset is None:
            return 0
        return self.offset

    @property
    def get_limit(self) -> int:
        if self.limit is None:
            return 20
        return self.limit

    @validator("sort", pre=True)
    def validate_sort(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if v not in ("asc", "desc"):
                raise ValueError('sort must be "asc" or "desc"')
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
    if sort is not None:
        column, sort_direction = sort
        if sort_direction.lower() == "desc":
            query = query.order_by(desc(column))
        else:
            query = query.order_by(asc(column))

    paginated = query.limit(limit).offset(offset)

    # seperate query for getting the total count
    count_stmt = select(func.count()).select_from(query.alias())

    # fetch both query results and combine
    results = session.execute(paginated).scalars().all()
    total_count = session.execute(count_stmt).scalar_one()
    return PaginatedQueryResult(items=list(results), total_count=total_count)
