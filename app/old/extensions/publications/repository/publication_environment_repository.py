import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationEnvironmentTable


class PublicationEnvironmentRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationEnvironmentTable]:
        stmt = select(PublicationEnvironmentTable).where(PublicationEnvironmentTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        is_active: Optional[bool],
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if is_active is not None:
            filters.append(and_(PublicationEnvironmentTable.Is_Active == is_active))

        stmt = select(PublicationEnvironmentTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationEnvironmentTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
