from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationAnnouncementTable


class PublicationAnnouncementRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuidx: UUID) -> Optional[PublicationAnnouncementTable]:
        stmt = select(PublicationAnnouncementTable).where(PublicationAnnouncementTable.UUID == uuidx)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        act_package_uuid: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = []
        if act_package_uuid is not None:
            filters.append(and_(PublicationAnnouncementTable.Act_Package_UUID == act_package_uuid))

        stmt = select(PublicationAnnouncementTable).filter(*filters)

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationAnnouncementTable.Modified_Date, SortOrder.DESC),
        )
        return paged_result
