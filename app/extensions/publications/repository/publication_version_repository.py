from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationVersionTable


class PublicationVersionRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationVersionTable]:
        stmt = select(PublicationVersionTable).where(PublicationVersionTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        publication_uuid: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = [PublicationVersionTable.Deleted_At.is_(None)]
        if publication_uuid is not None:
            filters.append(and_(PublicationVersionTable.Publication_UUID == publication_uuid))

        stmt = (
            select(PublicationVersionTable).filter(*filters).options(selectinload(PublicationVersionTable.Act_Packages))
        )

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationVersionTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
