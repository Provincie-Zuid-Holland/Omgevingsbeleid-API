from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import HoofdlijnTable


class HoofdlijnSortColumn(str, Enum):
    Created_Date = "Created_Date"
    Name = "Name"
    Type = "Type"


class HoofdlijnRepository(BaseRepository):
    def get_paginated(
        self,
        session: Session,
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        stmt = select(HoofdlijnTable)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
