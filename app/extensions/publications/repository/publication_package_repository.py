from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationPackageTable


class PublicationPackageRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationPackageTable]:
        stmt = select(PublicationPackageTable).filter(PublicationPackageTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        version_uuid: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if version_uuid is not None:
            filters.append(and_(PublicationPackageTable.Publication_Version_UUID == version_uuid))

        stmt = select(PublicationPackageTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationPackageTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
