from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import PackageType
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationActTable,
    PublicationActVersionTable,
    PublicationTable,
    PublicationVersionTable,
)


class PublicationActPackageRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, uuid: UUID) -> PublicationActPackageTable | None:
        publication = selectinload(PublicationActPackageTable.publication_version).selectinload(
            PublicationVersionTable.publication
        )
        stmt = (
            select(PublicationActPackageTable)
            .options(
                publication.selectinload(PublicationTable.environment),
                publication.selectinload(PublicationTable.act).selectinload(PublicationActTable.environment),
                selectinload(PublicationActPackageTable.module),
                selectinload(PublicationActPackageTable.module_status),
                selectinload(PublicationActPackageTable.zip),
                selectinload(PublicationActPackageTable.created_environment_state),
                selectinload(PublicationActPackageTable.act_version).selectinload(PublicationActVersionTable.act),
            )
            .filter(PublicationActPackageTable.id == uuid)
        )
        return await self.fetch_first(session, stmt)

    async def get_by_act_version(
        self, session: AsyncSession, act_version_id: UUID
    ) -> PublicationActPackageTable | None:
        stmt = select(PublicationActPackageTable).filter(PublicationActPackageTable.act_version_id == act_version_id)
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        version_id: UUID | None = None,
        package_type: PackageType | None = None,
    ) -> PaginatedQueryResult:
        filters = []
        if version_id is not None:
            filters.append(and_(PublicationActPackageTable.publication_version_id == version_id))

        if package_type is not None:
            filters.append(and_(PublicationActPackageTable.package_type == package_type.value))

        stmt = (
            select(PublicationActPackageTable)
            .options(
                selectinload(PublicationActPackageTable.zip),
                selectinload(PublicationActPackageTable.module_status),
            )
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
