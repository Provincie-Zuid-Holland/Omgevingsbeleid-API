from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import PackageType
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationTable,
    PublicationVersionTable,
)


class PublicationAnnouncementPackageRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, uuid: UUID) -> PublicationAnnouncementPackageTable | None:
        act_package = selectinload(PublicationAnnouncementPackageTable.announcement).selectinload(
            PublicationAnnouncementTable.act_package
        )
        stmt = (
            select(PublicationAnnouncementPackageTable)
            .options(
                act_package.selectinload(PublicationActPackageTable.publication_version)
                .selectinload(PublicationVersionTable.publication)
                .selectinload(PublicationTable.environment),
                act_package.selectinload(PublicationActPackageTable.module),
                act_package.selectinload(PublicationActPackageTable.module_status),
                selectinload(PublicationAnnouncementPackageTable.announcement)
                .selectinload(PublicationAnnouncementTable.publication)
                .selectinload(PublicationTable.environment),
                selectinload(PublicationAnnouncementPackageTable.zip),
                selectinload(PublicationAnnouncementPackageTable.created_environment_state),
            )
            .filter(PublicationAnnouncementPackageTable.id == uuid)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        announcement_id: UUID | None = None,
        package_type: PackageType | None = None,
    ) -> PaginatedQueryResult:
        filters = []
        if announcement_id is not None:
            filters.append(and_(PublicationAnnouncementPackageTable.announcement_id == announcement_id))

        if package_type is not None:
            filters.append(and_(PublicationAnnouncementPackageTable.package_type == package_type.value))

        stmt = (
            select(PublicationAnnouncementPackageTable)
            .options(selectinload(PublicationAnnouncementPackageTable.zip))
            .filter(*filters)
        )

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )
        return paged_result
