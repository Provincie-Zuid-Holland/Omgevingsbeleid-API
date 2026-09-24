from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortOrder
from app.core.tables.publications import PublicationVersionTable


class PublicationVersionRepository(BaseRepository):
    def get_by_uuid(self, session: Session, uuid: UUID) -> PublicationVersionTable | None:
        stmt = select(PublicationVersionTable).where(PublicationVersionTable.id == uuid)
        return self.fetch_first(session, stmt)

    def get_with_filters(
        self,
        session: Session,
        publication_uuid: UUID | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedQueryResult:
        filters = [PublicationVersionTable.deleted_at.is_(None)]
        if publication_uuid is not None:
            filters.append(and_(PublicationVersionTable.publication_id == publication_uuid))

        stmt = (
            select(PublicationVersionTable).filter(*filters).options(selectinload(PublicationVersionTable.act_packages))
        )

        paged_result = self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=offset,
            limit=limit,
            sort=(PublicationVersionTable.modified_date, SortOrder.DESC),
        )
        return paged_result
