import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationTemplateTable


class PublicationTemplateRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationTemplateTable]:
        stmt = select(PublicationTemplateTable).where(PublicationTemplateTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        only_active: bool,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if only_active:
            filters.append(and_(PublicationTemplateTable.Is_Active == True))

        stmt = select(PublicationTemplateTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTemplateTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
