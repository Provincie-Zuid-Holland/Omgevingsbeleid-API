import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationAreaOfJurisdictionTable


class PublicationAOJRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: uuid.UUID) -> PublicationAreaOfJurisdictionTable | None:
        stmt = select(PublicationAreaOfJurisdictionTable).where(PublicationAreaOfJurisdictionTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        stmt = select(PublicationAreaOfJurisdictionTable)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAreaOfJurisdictionTable.created_date, SortOrder.DESC),
        )
        return paged_result

    async def get_latest(
        self, session: AsyncSession, before_datetime: datetime | None = None
    ) -> PublicationAreaOfJurisdictionTable | None:
        stmt = (
            select(PublicationAreaOfJurisdictionTable)
            .order_by(desc(PublicationAreaOfJurisdictionTable.created_date))
            .limit(1)
        )
        if before_datetime:
            stmt = stmt.where(PublicationAreaOfJurisdictionTable.created_date <= before_datetime)
        return await self.fetch_first(session, stmt)
