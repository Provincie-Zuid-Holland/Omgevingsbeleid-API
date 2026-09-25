from uuid import UUID

from sqlalchemy import literal, select, union_all
from sqlalchemy.orm import Session

from app.api.domains.publications.types.enums import DocumentType, PackageType, PublicationType, ReportStatusType
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination, query_paginated_no_scalars
from app.core.tables.modules import ModuleTable
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)


class UnifiedPackagesProvider:
    def _build_act_packages_query(self):
        return (
            select(
                literal("act").label("Publication_Type"),
                PublicationActPackageTable.id,
                PublicationActPackageTable.created_date,
                PublicationActPackageTable.modified_date,
                PublicationActPackageTable.package_type,
                PublicationActPackageTable.report_status,
                PublicationActPackageTable.delivery_id,
                ModuleTable.module_id,
                ModuleTable.title.label("Module_Title"),
                PublicationTable.document_type,
                PublicationEnvironmentTable.id.label("Environment_UUID"),
            )
            .select_from(PublicationActPackageTable)
            .join(PublicationActPackageTable.publication_version)
            .join(PublicationVersionTable.publication)
            .join(PublicationTable.module)
            .join(PublicationTable.environment)
        )

    def _build_announcement_packages_query(self):
        return (
            select(
                literal("announcement").label("Publication_Type"),
                PublicationAnnouncementPackageTable.id,
                PublicationAnnouncementPackageTable.created_date,
                PublicationAnnouncementPackageTable.modified_date,
                PublicationAnnouncementPackageTable.package_type,
                PublicationAnnouncementPackageTable.report_status,
                PublicationAnnouncementPackageTable.delivery_id,
                ModuleTable.module_id,
                ModuleTable.title.label("Module_Title"),
                PublicationTable.document_type,
                PublicationEnvironmentTable.id.label("Environment_UUID"),
            )
            .select_from(PublicationAnnouncementPackageTable)
            .join(PublicationAnnouncementPackageTable.announcement)
            .join(PublicationAnnouncementTable.publication)
            .join(PublicationTable.module)
            .join(PublicationTable.environment)
        )

    def get_unified_packages(
        self,
        session: Session,
        pagination: SortedPagination,
        environment_uuid: UUID | None = None,
        module_id: int | None = None,
        report_status: ReportStatusType | None = None,
        package_type: PackageType | None = None,
        document_type: DocumentType | None = None,
        publication_type: PublicationType | None = None,
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
            stmt = stmt.filter(combined.c.environment_id == environment_uuid)
        if module_id:
            stmt = stmt.filter(combined.c.module_id == module_id)
        if report_status:
            stmt = stmt.filter(combined.c.report_status == report_status.value)
        if package_type:
            stmt = stmt.filter(combined.c.package_type == package_type.value)
        if document_type:
            stmt = stmt.filter(combined.c.document_type == document_type.value)

        return query_paginated_no_scalars(
            query=stmt,
            session=session,
            limit=pagination.limit,
            offset=pagination.offset,
            sort=(getattr(combined.c, pagination.sort.column), pagination.sort.order),
        )
