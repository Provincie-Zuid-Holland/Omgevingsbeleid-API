import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationAreaOfJurisdictionTable


class PublicationAOJRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: uuid.UUID) -> Optional[PublicationAreaOfJurisdictionTable]:
        stmt = select(PublicationAreaOfJurisdictionTable).where(PublicationAreaOfJurisdictionTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        stmt = select(PublicationAreaOfJurisdictionTable)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAreaOfJurisdictionTable.Created_Date, SortOrder.DESC),
        )
        return paged_result

    def get_latest(
        self, session: Session, before_datetime: Optional[datetime] = None
    ) -> Optional[PublicationAreaOfJurisdictionTable]:
        stmt = (
            select(PublicationAreaOfJurisdictionTable)
            .order_by(desc(PublicationAreaOfJurisdictionTable.Created_Date))
            .limit(1)
        )
        if before_datetime:
            stmt = stmt.where(PublicationAreaOfJurisdictionTable.Created_Date <= before_datetime)
        return self.fetch_first(session, stmt)
