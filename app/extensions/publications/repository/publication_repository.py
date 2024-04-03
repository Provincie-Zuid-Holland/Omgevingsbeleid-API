from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.tables.tables import PublicationTable


class PublicationRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[PublicationTable]:
        stmt = select(PublicationTable).where(PublicationTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        document_type: Optional[DocumentType] = None,
        module_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if document_type is not None:
            filters.append(and_(PublicationTable.Document_Type == document_type))
        if module_id is not None:
            filters.append(and_(PublicationTable.Module_ID == module_id))

        stmt = select(PublicationTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
