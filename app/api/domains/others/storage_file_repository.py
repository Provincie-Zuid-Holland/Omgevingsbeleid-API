from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, select

from app.api.base_repository import BaseRepository
from app.api.utils.pagination import PaginatedQueryResult, SimplePagination, SortOrder
from app.core.tables.others import StorageFileTable


class StorageFileSortColumn(str, Enum):
    Created_Date = "Created_Date"
    Filename = "Filename"
    Size = "Size"


class StorageFileSort(BaseModel):
    column: StorageFileSortColumn
    order: SortOrder


class StorageFileSortedPagination(SimplePagination):
    sort: StorageFileSort


class StorageFileRepository(BaseRepository):
    def get_by_uuid(self, uuidx: UUID) -> Optional[StorageFileTable]:
        stmt = select(StorageFileTable).filter(StorageFileTable.UUID == uuidx)
        return self.fetch_first(stmt)

    def get_by_checksum_uuid(self, checksum: str) -> Optional[StorageFileTable]:
        lookup: str = checksum[0:10]
        stmt = (
            select(StorageFileTable)
            .filter(StorageFileTable.Lookup == lookup)
            .filter(StorageFileTable.Checksum == checksum)
        )
        return self.fetch_first(stmt)

    def get_with_filters(
        self,
        pagination: StorageFileSortedPagination,
        filter_filename: Optional[str] = None,
        mine: Optional[UUID] = None,
    ) -> PaginatedQueryResult:
        filters = []
        if filter_filename is not None:
            filters.append(and_(StorageFileTable.Filename.like(filter_filename)))

        if mine is not None:
            filters.append(and_(StorageFileTable.Created_By_UUID == mine))

        stmt = select(StorageFileTable).filter(*filters)

        paged_result = self.fetch_paginated(
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(StorageFileTable, pagination.sort.column), pagination.sort.order),
        )
        return paged_result
