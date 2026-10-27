import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationEnvironmentStateTable, PublicationEnvironmentTable


class PublicationEnvironmentRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: uuid.UUID) -> PublicationEnvironmentTable | None:
        stmt = select(PublicationEnvironmentTable).where(PublicationEnvironmentTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_state_by_id(self, session: AsyncSession, idx: uuid.UUID) -> PublicationEnvironmentStateTable | None:
        stmt = select(PublicationEnvironmentStateTable).where(PublicationEnvironmentStateTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        is_active: bool | None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if is_active is not None:
            filters.append(and_(PublicationEnvironmentTable.is_active == is_active))

        stmt = select(PublicationEnvironmentTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationEnvironmentTable.modified_date, SortOrder.DESC),
        )
        return paged_result
