from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import HoofdlijnTable


class HoofdlijnRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> HoofdlijnTable | None:
        stmt = select(HoofdlijnTable).filter(HoofdlijnTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_by_ids(self, session: AsyncSession, ids: set[UUID]) -> set[UUID]:
        stmt = select(HoofdlijnTable.id).filter(HoofdlijnTable.id.in_(ids))
        return set(await self.fetch_all(session, stmt))

    async def get_paginated(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
    ) -> PaginatedQueryResult:
        stmt = select(HoofdlijnTable)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result

    async def search_by_name(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        query: str,
    ) -> PaginatedQueryResult:
        stmt = select(HoofdlijnTable).where(HoofdlijnTable.name.like(f"%{query}%"))

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(HoofdlijnTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
