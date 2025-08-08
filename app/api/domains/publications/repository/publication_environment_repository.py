import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationEnvironmentTable


class PublicationEnvironmentRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> Optional[PublicationEnvironmentTable]:
        stmt = select(PublicationEnvironmentTable).where(PublicationEnvironmentTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_active(self, session: Session, uuidx: uuid.UUID) -> Optional[PublicationEnvironmentTable]:
        stmt = select(PublicationEnvironmentTable).where(
            PublicationEnvironmentTable.UUID == uuidx,
            PublicationEnvironmentTable.Is_Active == True,
        )
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        is_active: Optional[bool],
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if is_active is not None:
            filters.append(and_(PublicationEnvironmentTable.Is_Active == is_active))

        stmt = select(PublicationEnvironmentTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationEnvironmentTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
