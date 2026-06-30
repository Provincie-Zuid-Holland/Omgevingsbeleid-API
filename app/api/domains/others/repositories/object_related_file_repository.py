from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import ObjectRelatedFileTable


class ObjectRelatedFileSortColumn(str, Enum):
    Created_Date = "Created_Date"
    Title = "Title"


class ObjectRelatedFileRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: UUID) -> Optional[ObjectRelatedFileTable]:
        stmt = select(ObjectRelatedFileTable).filter(ObjectRelatedFileTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_by_object_code(self, session: Session, object_code: str) -> List[ObjectRelatedFileTable]:
        stmt = (
            select(ObjectRelatedFileTable)
            .filter(ObjectRelatedFileTable.Object_Code == object_code)
            .order_by(ObjectRelatedFileTable.Created_Date.desc())
        )
        return self.fetch_all(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        pagination: SortedPagination,
        object_code: Optional[str] = None,
    ) -> PaginatedQueryResult:
        filters = []
        if object_code is not None:
            filters.append(ObjectRelatedFileTable.Object_Code == object_code)

        stmt = select(ObjectRelatedFileTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(ObjectRelatedFileTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
