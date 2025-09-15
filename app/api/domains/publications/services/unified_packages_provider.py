from typing import Optional
from uuid import UUID

from sqlalchemy import select, union_all, literal
from sqlalchemy.orm import Session

from app.api.utils.pagination import PaginatedQueryResult, SortedPagination, query_paginated_no_scalars
from app.api.domains.publications.types.enums import PublicationType, ReportStatusType, PackageType, DocumentType
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationVersionTable,
    PublicationTable,
    PublicationAnnouncementTable,
    PublicationEnvironmentTable,
)
from app.core.tables.modules import ModuleTable


class UnifiedPackagesProvider:
    def _build_act_packages_query(self):
        return (
            select(
                literal("act").label("Publication_Type"),
                PublicationActPackageTable.UUID,
                PublicationActPackageTable.Created_Date,
                PublicationActPackageTable.Modified_Date,
                PublicationActPackageTable.Package_Type,
                PublicationActPackageTable.Report_Status,
                PublicationActPackageTable.Delivery_ID,
                ModuleTable.Module_ID,
                ModuleTable.Title.label("Module_Title"),
                PublicationTable.Document_Type,
                PublicationEnvironmentTable.UUID.label("Environment_UUID"),
            )
            .select_from(PublicationActPackageTable)
            .join(PublicationActPackageTable.Publication_Version)
            .join(PublicationVersionTable.Publication)
            .join(PublicationTable.Module)
            .join(PublicationTable.Environment)
        )

    def _build_announcement_packages_query(self):
        return (
            select(
                literal("announcement").label("Publication_Type"),
                PublicationAnnouncementPackageTable.UUID,
                PublicationAnnouncementPackageTable.Created_Date,
                PublicationAnnouncementPackageTable.Modified_Date,
                PublicationAnnouncementPackageTable.Package_Type,
                PublicationAnnouncementPackageTable.Report_Status,
                PublicationAnnouncementPackageTable.Delivery_ID,
                ModuleTable.Module_ID,
                ModuleTable.Title.label("Module_Title"),
                PublicationTable.Document_Type,
                PublicationEnvironmentTable.UUID.label("Environment_UUID"),
            )
            .select_from(PublicationAnnouncementPackageTable)
            .join(PublicationAnnouncementPackageTable.Announcement)
            .join(PublicationAnnouncementTable.Publication)
            .join(PublicationTable.Module)
            .join(PublicationTable.Environment)
        )

    def get_unified_packages(
        self,
        session: Session,
        pagination: SortedPagination,
        environment_uuid: Optional[UUID] = None,
        module_id: Optional[int] = None,
        report_status: Optional[ReportStatusType] = None,
        package_type: Optional[PackageType] = None,
        document_type: Optional[DocumentType] = None,
        publication_type: Optional[PublicationType] = None,
    ) -> PaginatedQueryResult:
        combined = union_all(
            # alias().select() is a cheat to force parentheses
            # Else the union might fail on sqlite
            self._build_act_packages_query().alias().select(),
            self._build_announcement_packages_query().alias().select(),
        ).subquery()
        stmt = select(combined)

        if publication_type:
            stmt = stmt.filter(combined.c.Publication_Type == publication_type.value)
        if environment_uuid:
            stmt = stmt.filter(combined.c.Environment_UUID == environment_uuid)
        if module_id:
            stmt = stmt.filter(combined.c.Module_ID == module_id)
        if report_status:
            stmt = stmt.filter(combined.c.Report_Status == report_status.value)
        if package_type:
            stmt = stmt.filter(combined.c.Package_Type == package_type.value)
        if document_type:
            stmt = stmt.filter(combined.c.Document_Type == document_type.value)

        return query_paginated_no_scalars(
            query=stmt,
            session=session,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(combined.c, pagination.sort.column), pagination.sort.order),
        )
