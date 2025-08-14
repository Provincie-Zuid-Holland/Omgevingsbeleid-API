from typing import Optional
from uuid import UUID

from sqlalchemy import and_, literal, select
from sqlalchemy.orm import Session, aliased

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import DocumentType, PackageType, ReportStatusType
from app.api.types import Selectable
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.modules import ModuleTable
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationPackageZipTable,
    PublicationTable,
    PublicationVersionTable,
)
from app.api.domains.publications.types.filters import PublicationPackageFilters
from .filters import apply_package_overview_filters


class PublicationActPackageRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(PublicationActPackageTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_act_version(self, session: Session, act_version_uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(
            PublicationActPackageTable.Act_Version_UUID == act_version_uuid
        )
        result: Optional[PublicationActPackageTable] = self.fetch_first(session, stmt)
        return result

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        version_uuid: Optional[UUID] = None,
        package_type: Optional[PackageType] = None,
    ) -> PaginatedQueryResult:
        filters = []
        if version_uuid is not None:
            filters.append(and_(PublicationActPackageTable.Publication_Version_UUID == version_uuid))

        if package_type is not None:
            filters.append(and_(PublicationActPackageTable.Package_Type == package_type.value))

        stmt = select(PublicationActPackageTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )
        return paged_result

    def build_overview_query(
        self,
        filters: Optional[PublicationPackageFilters] = None,
        package_uuid: Optional[UUID] = None,
    ) -> Selectable:
        actp = aliased(PublicationActPackageTable)
        pv = aliased(PublicationVersionTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)
        z = aliased(PublicationPackageZipTable)

        query = (
            select(
                actp.UUID.label("UUID"),
                actp.Package_Type.label("Package_Type"),
                actp.Report_Status.label("Report_Status"),
                actp.Delivery_ID.label("Delivery_ID"),
                actp.Created_Date.label("Created_Date"),
                actp.Created_By_UUID.label("Created_By_UUID"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Module_ID"),
                m.Title.label("Module_Title"),
                literal("act").label("Package_Category"),
                p.Environment_UUID.label("Publication_Environment_UUID"),
                actp.Zip_UUID.label("Zip_UUID"),
                z.Filename.label("Filename"),
            )
            .select_from(actp)
            .join(pv, actp.Publication_Version_UUID == pv.UUID)
            .join(p, pv.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
            .join(z, actp.Zip_UUID == z.UUID)
        )

        return self._apply_overview_filters(query, p, actp, filters, package_uuid)

    def build_detail_query(self, package_uuid: UUID) -> Selectable:
        actp = aliased(PublicationActPackageTable)
        pv = aliased(PublicationVersionTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)
        z = aliased(PublicationPackageZipTable)

        query = (
            select(
                actp.UUID.label("UUID"),
                actp.Package_Type.label("Package_Type"),
                actp.Report_Status.label("Report_Status"),
                actp.Delivery_ID.label("Delivery_ID"),
                actp.Created_Date.label("Created_Date"),
                actp.Created_By_UUID.label("Created_By_UUID"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Module_ID"),
                m.Title.label("Module_Title"),
                p.Environment_UUID.label("Publication_Environment_UUID"),
                actp.Zip_UUID.label("Zip_UUID"),
                z.Filename.label("Filename"),
            )
            .select_from(actp)
            .join(pv, actp.Publication_Version_UUID == pv.UUID)
            .join(p, pv.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
            .join(z, actp.Zip_UUID == z.UUID)
            .filter(actp.UUID == package_uuid)
        )

        return query

    def _apply_overview_filters(
        self,
        query: Selectable,
        publication_alias: PublicationTable,
        package_alias: PublicationActPackageTable,
        filters: Optional[PublicationPackageFilters] = None,
        package_uuid: Optional[UUID] = None,
    ) -> Selectable:
        return apply_package_overview_filters(query, publication_alias, package_alias, filters, package_uuid)
