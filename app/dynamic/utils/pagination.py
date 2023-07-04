from dataclasses import dataclass
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


@dataclass
class Pagination:
    offset: Optional[int] = None
    limit: Optional[int] = None

    def get_offset(self) -> int:
        if self.offset is None:
            return 0
        return self.offset

    def get_limit(self) -> int:
        if self.limit is None:
            return 20
        return self.limit


T = TypeVar("T", bound=BaseModel)


class PagedResponse(GenericModel, Generic[T]):
    """
    Wrap any response schema and add pagination metadata.
    """

    total: int
    offset: int = 0
    limit: int = -1
    results: List[T]


@dataclass
class PaginatedQueryResult:
    items: Any
    total_count: int = 0


def query_paginated(query: Select, session: Session, limit=-1, offset=0):
    """
    Extend a query with pagination and wrap the query results
    in a generic response containing pagination meta data.
    """
    # build paginated query
    paginated = query.limit(limit).offset(offset)
    # query for getting the total count
    count_stmt = select(func.count()).select_from(query.alias())

    # fetch results
    results = session.execute(paginated).scalars().all()
    total_count = session.execute(count_stmt).scalar_one()

    return PaginatedQueryResult(results, total_count)
