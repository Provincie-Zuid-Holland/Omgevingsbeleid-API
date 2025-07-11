from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import PackageType
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.publications import PublicationAnnouncementPackageTable


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
