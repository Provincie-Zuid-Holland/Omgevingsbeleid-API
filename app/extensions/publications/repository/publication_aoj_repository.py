import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select

from app.dynamic.repository.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult, SortOrder
from app.extensions.publications.tables.tables import PublicationAreaOfJurisdictionTable


class PublicationAOJRepository(BaseRepository):
    def get_by_uuid(self, uuidx: uuid.UUID) -> Optional[PublicationAreaOfJurisdictionTable]:
        stmt = select(PublicationAreaOfJurisdictionTable).where(PublicationAreaOfJurisdictionTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        stmt = select(PublicationAreaOfJurisdictionTable)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAreaOfJurisdictionTable.Created_Date, SortOrder.DESC),
        )
        return paged_result

    def get_latest(self, before_datetime: Optional[datetime] = None) -> Optional[PublicationAreaOfJurisdictionTable]:
        stmt = (
            select(PublicationAreaOfJurisdictionTable)
            .order_by(desc(PublicationAreaOfJurisdictionTable.Created_Date))
            .limit(1)
        )
        if before_datetime:
            stmt = stmt.where(PublicationAreaOfJurisdictionTable.Created_Date < before_datetime)
        return self.fetch_first(stmt)
