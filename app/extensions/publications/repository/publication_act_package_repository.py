from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationActPackageTable


class PublicationActPackageRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(PublicationActPackageTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_by_act_version(self, act_version_uuid: UUID) -> Optional[PublicationActPackageTable]:
        stmt = select(PublicationActPackageTable).filter(
            PublicationActPackageTable.Act_Version_UUID == act_version_uuid
        )
        result: Optional[PublicationActPackageTable] = self.fetch_first(stmt)
        return result

    def get_with_filters(
        self,
        version_uuid: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if version_uuid is not None:
            filters.append(and_(PublicationActPackageTable.Publication_Version_UUID == version_uuid))

        stmt = select(PublicationActPackageTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationActPackageTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
