import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.tables.tables import PublicationPackageReportTable


class PublicationReportRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationPackageReportTable]:
        stmt = select(PublicationPackageReportTable).where(PublicationPackageReportTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        package_uuid: Optional[uuid.UUID] = None,
        filename: Optional[str] = None,
        report_status: Optional[ReportStatusType] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if package_uuid is not None:
            filters.append(and_(PublicationPackageReportTable.Package_UUID == package_uuid))
        if filename is not None:
            filters.append(and_(PublicationPackageReportTable.Filename == filename))
        if report_status is not None:
            filters.append(and_(PublicationPackageReportTable.Report_Status == report_status.value))

        stmt = select(PublicationPackageReportTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationPackageReportTable.Created_Date, SortOrder.DESC),
        )
        return paged_result
