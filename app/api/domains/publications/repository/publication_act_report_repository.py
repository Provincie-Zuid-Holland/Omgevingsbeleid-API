import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import ReportStatusType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationActPackageReportTable


class PublicationActReportRepository(BaseRepository):
    def get_by_id(self, session: Session, idx: uuid.UUID) -> PublicationActPackageReportTable | None:
        stmt = select(PublicationActPackageReportTable).where(PublicationActPackageReportTable.id == idx)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        act_package_uuid: uuid.UUID | None = None,
        filename: str | None = None,
        report_status: ReportStatusType | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if act_package_uuid is not None:
            filters.append(and_(PublicationActPackageReportTable.act_package_id == act_package_uuid))
        if filename is not None:
            filters.append(and_(PublicationActPackageReportTable.filename == filename))
        if report_status is not None:
            filters.append(and_(PublicationActPackageReportTable.report_status == report_status.value))

        stmt = select(PublicationActPackageReportTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationActPackageReportTable.created_date, SortOrder.DESC),
        )
        return paged_result
