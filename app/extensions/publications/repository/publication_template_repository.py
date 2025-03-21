import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.tables.tables import PublicationTemplateTable


class PublicationTemplateRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationTemplateTable]:
        stmt = select(PublicationTemplateTable).where(PublicationTemplateTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        is_active: Optional[bool],
        document_type: Optional[DocumentType],
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if is_active is not None:
            filters.append(and_(PublicationTemplateTable.Is_Active == is_active))
        if document_type is not None:
            filters.append(and_(PublicationTemplateTable.Document_Type == document_type.value))

        stmt = select(PublicationTemplateTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTemplateTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
