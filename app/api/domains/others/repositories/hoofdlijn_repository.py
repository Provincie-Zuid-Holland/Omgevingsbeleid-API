from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import HoofdlijnTable


class HoofdlijnRepository(BaseRepository):
    def get_by_id(self, session: Session, idx: UUID) -> HoofdlijnTable | None:
        stmt = select(HoofdlijnTable).filter(HoofdlijnTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_by_ids(self, session: Session, ids: set[UUID]) -> set[UUID]:
        stmt = select(HoofdlijnTable.id).filter(HoofdlijnTable.id.in_(ids))
        return set(self.fetch_all(session, stmt))

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

    def search_by_name(
        self,
        session: Session,
        pagination: SortedPagination,
        query: str,
    ) -> PaginatedQueryResult:
        stmt = select(HoofdlijnTable).where(HoofdlijnTable.name.like(f"%{query}%"))

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
