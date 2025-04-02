from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortedPagination
from app.extensions.publications.enums import PackageType
from app.extensions.publications.tables.tables import PublicationAnnouncementPackageTable


class PublicationAnnouncementPackageRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationAnnouncementPackageTable]:
        stmt = select(PublicationAnnouncementPackageTable).filter(PublicationAnnouncementPackageTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
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
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(pagination.sort.column, pagination.sort.order),
        )
        return paged_result
