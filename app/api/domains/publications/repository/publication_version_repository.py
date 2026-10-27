from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationTable, PublicationVersionTable


class PublicationVersionRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, uuid: UUID) -> PublicationVersionTable | None:
        stmt = (
            select(PublicationVersionTable)
            .options(
                selectinload(PublicationVersionTable.publication).selectinload(PublicationTable.module),
                selectinload(PublicationVersionTable.publication).selectinload(PublicationTable.act),
                selectinload(PublicationVersionTable.publication).selectinload(PublicationTable.environment),
                selectinload(PublicationVersionTable.publication).selectinload(PublicationTable.template),
                selectinload(PublicationVersionTable.module_status),
                selectinload(PublicationVersionTable.attachments),
                selectinload(PublicationVersionTable.act_packages),
            )
            .where(PublicationVersionTable.id == uuid)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        publication_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = [PublicationVersionTable.deleted_at.is_(None)]
        if publication_id is not None:
            filters.append(and_(PublicationVersionTable.publication_id == publication_id))

        stmt = (
            select(PublicationVersionTable)
            .filter(*filters)
            .options(
                selectinload(PublicationVersionTable.act_packages),
                selectinload(PublicationVersionTable.module_status),
            )
        )

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationVersionTable.modified_date, SortOrder.DESC),
        )
        return paged_result
