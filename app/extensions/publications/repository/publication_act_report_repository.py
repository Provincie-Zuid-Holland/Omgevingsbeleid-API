import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.tables.tables import PublicationActPackageReportTable


class PublicationActReportRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationActPackageReportTable]:
        stmt = select(PublicationActPackageReportTable).where(PublicationActPackageReportTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        act_package_uuid: Optional[uuid.UUID] = None,
        filename: Optional[str] = None,
        report_status: Optional[ReportStatusType] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if act_package_uuid is not None:
            filters.append(and_(PublicationActPackageReportTable.Act_Package_UUID == act_package_uuid))
        if filename is not None:
            filters.append(and_(PublicationActPackageReportTable.Filename == filename))
        if report_status is not None:
            filters.append(and_(PublicationActPackageReportTable.Report_Status == report_status.value))

        stmt = select(PublicationActPackageReportTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationActPackageReportTable.Created_Date, SortOrder.DESC),
        )
        return paged_result
