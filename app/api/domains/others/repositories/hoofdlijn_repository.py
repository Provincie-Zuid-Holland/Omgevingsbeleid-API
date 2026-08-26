from enum import Enum
from uuid import UUID

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
    def get_by_uuid(self, session: Session, uuidx: UUID) -> HoofdlijnTable | None:
        stmt = select(HoofdlijnTable).filter(HoofdlijnTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        filter_deleted: bool | None = True,
    ) -> PaginatedQueryResult:
        stmt = select(HoofdlijnTable)
        if filter_deleted:
            stmt = stmt.where(HoofdlijnTable.Deleted_Date.is_(None))
        elif filter_deleted is False:
            stmt = stmt.where(HoofdlijnTable.Deleted_Date.is_not(None))

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result

    def search_by_name(
        self,
        session: Session,
        pagination: SortedPagination,
        query: str,
        filter_deleted: bool | None = True,
    ):
        stmt = select(HoofdlijnTable).where(HoofdlijnTable.Name.like(f"%{query}%"))
        if filter_deleted:
            stmt = stmt.where(HoofdlijnTable.Deleted_Date.is_(None))
        elif filter_deleted is False:
            stmt = stmt.where(HoofdlijnTable.Deleted_Date.is_not(None))

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
