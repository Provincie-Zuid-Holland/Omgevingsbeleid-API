from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import ObjectRelatedFileTable


class ObjectRelatedFileSortColumn(str, Enum):
    created_date = "created_date"
    Title = "Title"


class ObjectRelatedFileRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> ObjectRelatedFileTable | None:
        stmt = (
            select(ObjectRelatedFileTable)
            .options(selectinload(ObjectRelatedFileTable.object_statics))
            .filter(ObjectRelatedFileTable.id == idx)
        )
        return await self.fetch_first(session, stmt)

    async def get_by_object_code(self, session: AsyncSession, object_code: str) -> list[ObjectRelatedFileTable]:
        stmt = (
            select(ObjectRelatedFileTable)
            .filter(ObjectRelatedFileTable.code == object_code)
            .order_by(ObjectRelatedFileTable.created_date.desc())
        )
        return await self.fetch_all(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        object_code: str | None = None,
    ) -> PaginatedQueryResult:
        filters = []
        if object_code is not None:
            filters.append(ObjectRelatedFileTable.code == object_code)

        stmt = select(ObjectRelatedFileTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(ObjectRelatedFileTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
