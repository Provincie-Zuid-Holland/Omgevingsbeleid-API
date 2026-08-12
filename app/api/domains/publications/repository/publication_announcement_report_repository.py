import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationAnnouncementPackageReportTable


class PublicationAnnouncementReportRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> PublicationAnnouncementPackageReportTable | None:
        stmt = select(PublicationAnnouncementPackageReportTable).where(
            PublicationAnnouncementPackageReportTable.UUID == uuidx
        )
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        announcement_package_uuid: uuid.UUID | None = None,
        filename: str | None = None,
        report_status: ReportStatusType | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if announcement_package_uuid is not None:
            filters.append(
                and_(PublicationAnnouncementPackageReportTable.Announcement_Package_UUID == announcement_package_uuid)
            )
        if filename is not None:
            filters.append(and_(PublicationAnnouncementPackageReportTable.Filename == filename))
        if report_status is not None:
            filters.append(and_(PublicationAnnouncementPackageReportTable.Report_Status == report_status.value))

        stmt = select(PublicationAnnouncementPackageReportTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAnnouncementPackageReportTable.Created_Date, SortOrder.DESC),
        )
        return paged_result
