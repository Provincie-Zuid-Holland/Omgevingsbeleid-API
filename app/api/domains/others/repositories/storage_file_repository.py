from collections.abc import Sequence
from enum import Enum
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.others import StorageFileTable


class StorageFileSortColumn(str, Enum):
    created_date = "created_date"
    Filename = "Filename"
    Size = "Size"


class StorageFileRepository(BaseRepository):
    async def get_by_id(self, session: AsyncSession, idx: UUID) -> StorageFileTable | None:
        stmt = select(StorageFileTable).filter(StorageFileTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_with_binary(self, session: AsyncSession, idx: UUID) -> StorageFileTable | None:
        stmt = select(StorageFileTable).options(undefer(StorageFileTable.binary)).filter(StorageFileTable.id == idx)
        return await self.fetch_first(session, stmt)

    async def get_by_checksum_uuid(self, session: AsyncSession, checksum: str) -> StorageFileTable | None:
        lookup: str = checksum[0:10]
        stmt = (
            select(StorageFileTable)
            .filter(StorageFileTable.lookup == lookup)
            .filter(StorageFileTable.checksum == checksum)
        )
        return await self.fetch_first(session, stmt)

    async def get_with_filters(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        filter_filename: str | None = None,
        mine: UUID | None = None,
    ) -> PaginatedQueryResult:
        filters = []
        if filter_filename is not None:
            filters.append(and_(StorageFileTable.filename.like(filter_filename)))

        if mine is not None:
            filters.append(and_(StorageFileTable.created_by_id == mine))

        stmt = select(StorageFileTable).filter(*filters)

        paged_result = await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(StorageFileTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result

    async def get_all(self, session: AsyncSession) -> Sequence[StorageFileTable]:
        stmt = select(StorageFileTable)
        return await self.fetch_all(session, stmt)
