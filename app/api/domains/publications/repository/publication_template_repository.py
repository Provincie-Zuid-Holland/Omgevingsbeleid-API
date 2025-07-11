import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.publications.types.enums import DocumentType
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationTemplateTable


class PublicationTemplateRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> Optional[PublicationTemplateTable]:
        stmt = select(PublicationTemplateTable).where(PublicationTemplateTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
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
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationTemplateTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
