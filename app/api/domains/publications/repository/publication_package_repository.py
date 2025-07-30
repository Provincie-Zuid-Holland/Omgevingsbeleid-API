from typing import Optional
import uuid
from sqlalchemy import and_, literal, select
from sqlalchemy.orm import Session, aliased

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import DocumentType, PackageType, ReportStatusType
from app.api.types import Selectable
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.modules import ModuleTable
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationAnnouncementPackageTable,
    PublicationTable,
    PublicationVersionTable,
    PublicationAnnouncementTable,
)


class PublicationPackageRepository(BaseRepository):
    def get_act_packages(
        self,
        session: Session,
        pagination: SortedPagination,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None
    ) -> PaginatedQueryResult:
        query = self._build_act_packages_query(document_type, package_type, status_filter, environment_uuid)

        paged_result = self.fetch_paginated_no_scalars(
            session=session,
            statement=query,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )

        return paged_result

    def get_announcement_packages(
        self,
        session: Session,
        pagination: SortedPagination,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None
    ) -> PaginatedQueryResult:
        query = self._build_announcement_packages_query(document_type, package_type, status_filter, environment_uuid)

        paged_result = self.fetch_paginated_no_scalars(
            session=session,
            statement=query,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )

        return paged_result

    def get_all_packages(
        self,
        session: Session,
        pagination: SortedPagination,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None
    ) -> PaginatedQueryResult:
        act_query = self._build_act_packages_query(document_type, package_type, status_filter, environment_uuid)
        announcement_query = self._build_announcement_packages_query(document_type, package_type, status_filter, environment_uuid)

        query: Selectable = act_query.union(announcement_query)

        paged_result = self.fetch_paginated_no_scalars(
            session=session,
            statement=query,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )

        return paged_result

    def _apply_package_filters(
        self,
        query: Selectable,
        publication_alias: PublicationTable,
        package_alias: PublicationActPackageTable | PublicationAnnouncementPackageTable,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None,
    ) -> Selectable:
        filter_conditions = []

        if document_type is not None:
            filter_conditions.append(publication_alias.Document_Type == document_type.value)

        if package_type is not None:
            filter_conditions.append(package_alias.Package_Type == package_type.value)

        if status_filter:
            filter_conditions.append(package_alias.Report_Status == status_filter)

        if environment_uuid:
            filter_conditions.append(publication_alias.Environment_UUID == environment_uuid)

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        return query

    def _build_act_packages_query(
        self,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None,
    ) -> Selectable:
        actp = aliased(PublicationActPackageTable)
        pv = aliased(PublicationVersionTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)

        query = (
            select(
                actp.UUID.label("UUID"),
                actp.Package_Type.label("Package_Type"),
                actp.Report_Status.label("Report_Status"),
                actp.Delivery_ID.label("Delivery_ID"),
                actp.Created_Date.label("Created_Date"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Module_ID"),
                m.Title.label("Module_Title"),
                literal("act").label("Package_Category"),
            )
            .select_from(actp)
            .join(pv, actp.Publication_Version_UUID == pv.UUID)
            .join(p, pv.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
        )

        return self._apply_package_filters(query, p, actp, document_type, package_type, status_filter, environment_uuid)

    def _build_announcement_packages_query(
        self,
        document_type: Optional[DocumentType] = None,
        package_type: Optional[PackageType] = None,
        status_filter: Optional[ReportStatusType] = None,
        environment_uuid: Optional[uuid.UUID] = None,
    ) -> Selectable:
        anp = aliased(PublicationAnnouncementPackageTable)
        pa = aliased(PublicationAnnouncementTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)

        query = (
            select(
                anp.UUID.label("UUID"),
                anp.Package_Type.label("Package_Type"),
                anp.Report_Status.label("Report_Status"),
                anp.Delivery_ID.label("Delivery_ID"),
                anp.Created_Date.label("Created_Date"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Module_ID"),
                m.Title.label("Module_Title"),
                literal("announcement").label("Package_Category"),
            )
            .select_from(anp)
            .join(pa, anp.Announcement_UUID == pa.UUID)
            .join(p, pa.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
        )

        return self._apply_package_filters(query, p, anp, document_type, package_type, status_filter, environment_uuid)
