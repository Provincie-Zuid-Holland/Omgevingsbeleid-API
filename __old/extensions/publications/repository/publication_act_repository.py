import uuid
from typing import Optional

from sqlalchemy import and_, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.enums import DocumentType, ProcedureType
from app.extensions.publications.tables.tables import PublicationActTable


class PublicationActRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationActTable]:
        stmt = select(PublicationActTable).where(PublicationActTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        is_active: Optional[bool] = None,
        environment_uuid: Optional[uuid.UUID] = None,
        document_type: Optional[DocumentType] = None,
        procedure_type: Optional[ProcedureType] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if is_active is not None:
            filters.append(and_(PublicationActTable.Is_Active == is_active))
        if environment_uuid is not None:
            filters.append(and_(PublicationActTable.Environment_UUID == environment_uuid))
        if document_type is not None:
            filters.append(and_(PublicationActTable.Document_Type == document_type.value))
        if procedure_type is not None:
            filters.append(and_(PublicationActTable.Procedure_Type == procedure_type.value))

        stmt = select(PublicationActTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationActTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
