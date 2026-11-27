from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import DocumentType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationTable


class PublicationRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, uuid: UUID) -> PublicationTable | None:
        stmt = (
            select(PublicationTable)
            .options(
                selectinload(PublicationTable.module),
                selectinload(PublicationTable.act),
                selectinload(PublicationTable.environment),
            )
            .where(PublicationTable.id == uuid)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        document_type: DocumentType | None = None,
        module_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if document_type is not None:
            filters.append(and_(PublicationTable.document_type == document_type))
        if module_id is not None:
            filters.append(and_(PublicationTable.module_id == module_id))

        stmt = select(PublicationTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTable.modified_date, SortOrder.DESC),
        )
        return paged_result
