import uuid
from typing import Callable, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.utils.pagination import SortOrder
from app.extensions.storage_files.db.tables import StorageFileTable
from app.extensions.storage_files.repository.storage_file_repository import (
    StorageFileSort,
    StorageFileSortColumn,
    StorageFileSortedPagination,
)

from .repository import StorageFileRepository


def depends_storage_file_repository(
    db: Session = Depends(depends_db),
) -> StorageFileRepository:
    return StorageFileRepository(db)


def depends_storage_file(
    file_uuid: uuid.UUID,
    repository: StorageFileRepository = Depends(depends_storage_file_repository),
) -> StorageFileTable:
    maybe_file: Optional[StorageFileTable] = repository.get_by_uuid(file_uuid)
    if not maybe_file:
        raise HTTPException(status_code=404, detail="Storage file niet gevonden")
    return maybe_file


def depends_storage_file_sorted_pagination_curried(
    default_column: StorageFileSortColumn, default_order: SortOrder
) -> Callable:
    def depends_storage_file_sorted_pagination_curried_inner(
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort_column: Optional[StorageFileSortColumn] = None,
        sort_order: Optional[SortOrder] = None,
    ) -> StorageFileSortedPagination:
        column: StorageFileSortColumn = sort_column or default_column
        order: SortOrder = sort_order or default_order
        module_sort = StorageFileSort(column=column, order=order)

        pagination: StorageFileSortedPagination = StorageFileSortedPagination(
            offset=offset,
            limit=limit,
            sort=module_sort,
        )
        return pagination

    return depends_storage_file_sorted_pagination_curried_inner
