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
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationPackageZipTable,
    PublicationTable,
)
from app.api.domains.publications.types.filters import PublicationPackageFilters
from .filters import apply_package_overview_filters


class PublicationAnnouncementPackageRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[PublicationAnnouncementPackageTable]:
        stmt = select(PublicationAnnouncementPackageTable).filter(PublicationAnnouncementPackageTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        announcement_uuid: Optional[UUID] = None,
        package_type: Optional[PackageType] = None,
    ) -> PaginatedQueryResult:
        filters = []
        if announcement_uuid is not None:
            filters.append(and_(PublicationAnnouncementPackageTable.Announcement_UUID == announcement_uuid))

        if package_type is not None:
            filters.append(and_(PublicationAnnouncementPackageTable.Package_Type == package_type.value))

        stmt = select(PublicationAnnouncementPackageTable).filter(*filters)

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
        anp = aliased(PublicationAnnouncementPackageTable)
        pa = aliased(PublicationAnnouncementTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)
        z = aliased(PublicationPackageZipTable)

        query = (
            select(
                anp.UUID.label("UUID"),
                anp.Package_Type.label("Package_Type"),
                anp.Report_Status.label("Report_Status"),
                anp.Delivery_ID.label("Delivery_ID"),
                anp.Created_Date.label("Created_Date"),
                anp.Created_By_UUID.label("Created_By_UUID"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Module_ID"),
                m.Title.label("Module_Title"),
                literal("announcement").label("Package_Category"),
                p.Environment_UUID.label("Publication_Environment_UUID"),
                anp.Zip_UUID.label("Zip_UUID"),
                z.Filename.label("Filename"),
            )
            .select_from(anp)
            .join(pa, anp.Announcement_UUID == pa.UUID)
            .join(p, pa.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
            .join(z, anp.Zip_UUID == z.UUID)
        )

        return self._apply_overview_filters(
            query,
            p,
            anp,
            filters,
            package_uuid,
        )

    def build_detail_query(self, package_uuid: UUID) -> Selectable:
        anp = aliased(PublicationAnnouncementPackageTable)
        pa = aliased(PublicationAnnouncementTable)
        p = aliased(PublicationTable)
        m = aliased(ModuleTable)
        z = aliased(PublicationPackageZipTable)

        query = (
            select(
                anp.UUID.label("UUID"),
                anp.Package_Type.label("Package_Type"),
                anp.Report_Status.label("Report_Status"),
                anp.Delivery_ID.label("Delivery_ID"),
                anp.Created_Date.label("Created_Date"),
                anp.Created_By_UUID.label("Created_By_UUID"),
                p.Document_Type.label("Document_Type"),
                m.Module_ID.label("Mocould we make it a but cooler by also addeing the package_filter thats not in the filters depedency yet to it, or maybe subclassing the @PublicationPackageFilters , or maybe when passing it to the repositories for dule_ID"),
                m.Title.label("Module_Title"),
                p.Environment_UUID.label("Publication_Environment_UUID"),
                anp.Zip_UUID.label("Zip_UUID"),
                z.Filename.label("Filename"),
            )
            .select_from(anp)
            .join(pa, anp.Announcement_UUID == pa.UUID)
            .join(p, pa.Publication_UUID == p.UUID)
            .join(m, p.Module_ID == m.Module_ID)
            .join(z, anp.Zip_UUID == z.UUID)
            .filter(anp.UUID == package_uuid)
        )

        return query

    def _apply_overview_filters(
        self,
        query: Selectable,
        publication_alias: PublicationTable,
        package_alias: PublicationAnnouncementPackageTable,
        filters: Optional[PublicationPackageFilters] = None,
        package_uuid: Optional[UUID] = None,
    ) -> Selectable:
        return apply_package_overview_filters(query, publication_alias, package_alias, filters, package_uuid)
