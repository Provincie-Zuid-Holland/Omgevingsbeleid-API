import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationActPackageReportTable


class PublicationActReportRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: uuid.UUID) -> PublicationActPackageReportTable | None:
        stmt = select(PublicationActPackageReportTable).where(PublicationActPackageReportTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        act_package_id: uuid.UUID | None = None,
        filename: str | None = None,
        report_status: ReportStatusType | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if act_package_id is not None:
            filters.append(and_(PublicationActPackageReportTable.act_package_id == act_package_id))
        if filename is not None:
            filters.append(and_(PublicationActPackageReportTable.filename == filename))
        if report_status is not None:
            filters.append(and_(PublicationActPackageReportTable.report_status == report_status.value))

        stmt = select(PublicationActPackageReportTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationActPackageReportTable.created_date, SortOrder.DESC),
        )
        return paged_result
