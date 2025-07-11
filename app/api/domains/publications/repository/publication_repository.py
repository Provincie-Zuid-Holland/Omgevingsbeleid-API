from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import DocumentType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationTable


class PublicationRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[PublicationTable]:
        stmt = select(PublicationTable).where(PublicationTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
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
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
