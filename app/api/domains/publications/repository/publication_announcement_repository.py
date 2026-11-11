from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationActVersionTable,
    PublicationAnnouncementTable,
    PublicationBillVersionTable,
    PublicationTable,
)


class PublicationAnnouncementRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> PublicationAnnouncementTable | None:
        stmt = (
            select(PublicationAnnouncementTable)
            .options(
                joinedload(PublicationAnnouncementTable.publication).options(
                    joinedload(PublicationTable.module),
                    joinedload(PublicationTable.act),
                    joinedload(PublicationTable.environment),
                ),
                joinedload(PublicationAnnouncementTable.act_package).options(
                    joinedload(PublicationActPackageTable.publication_version),
                    joinedload(PublicationActPackageTable.act_version).joinedload(PublicationActVersionTable.act),
                    joinedload(PublicationActPackageTable.bill_version).joinedload(PublicationBillVersionTable.bill),
                ),
            )
            .where(PublicationAnnouncementTable.id == idx)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        act_package_id: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if act_package_id is not None:
            filters.append(and_(PublicationAnnouncementTable.act_package_id == act_package_id))

        stmt = select(PublicationAnnouncementTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAnnouncementTable.modified_date, SortOrder.DESC),
        )
        return paged_result
