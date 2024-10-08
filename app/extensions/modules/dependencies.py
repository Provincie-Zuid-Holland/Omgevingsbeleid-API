from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.dependencies import depends_object_repository
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.utils.pagination import SortOrder
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models import Module
from app.extensions.modules.repository import (
    ModuleObjectContextRepository,
    ModuleObjectRepository,
    ModuleRepository,
    ModuleStatusRepository,
)
from app.extensions.modules.repository.module_repository import ModuleSort, ModuleSortColumn, ModuleSortedPagination
from app.extensions.modules.repository.object_provider import ObjectProvider


def depends_module_repository(db: Session = Depends(depends_db)) -> ModuleRepository:
    return ModuleRepository(db)


def depends_module_status_repository(
    db: Session = Depends(depends_db),
) -> ModuleStatusRepository:
    return ModuleStatusRepository(db)


def depends_module_object_repository(
    db: Session = Depends(depends_db),
) -> ModuleObjectRepository:
    return ModuleObjectRepository(db)


def depends_module_object_context_repository(
    db: Session = Depends(depends_db),
) -> ModuleObjectContextRepository:
    return ModuleObjectContextRepository(db)


def depends_module(
    module_id: int,
    repository: ModuleRepository = Depends(depends_module_repository),
) -> ModuleTable:
    maybe_module: Optional[ModuleTable] = repository.get_by_id(module_id)
    if not maybe_module:
        raise HTTPException(status_code=404, detail="Module niet gevonden")
    return maybe_module


def depends_active_module(
    module: Module = Depends(depends_module),
) -> ModuleTable:
    if module.Closed:
        raise HTTPException(status_code=404, detail="De module is gesloten")
    return module


def depends_active_and_activated_module(
    module: Module = Depends(depends_active_module),
) -> ModuleTable:
    if not module.Activated:
        raise HTTPException(status_code=404, detail="De module is nog niet actief")
    return module


def depends_module_object_by_uuid_curried(object_type: str) -> Callable:
    def curry_depends_module_object_by_uuid(
        module_id: int,
        object_uuid: UUID,
        module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
    ):
        maybe_object: Optional[ModuleObjectsTable] = module_object_repository.get_by_module_id_object_type_and_uuid(
            module_id,
            object_type,
            object_uuid,
        )
        if not maybe_object:
            raise HTTPException(status_code=404, detail="Module Object niet gevonden")
        return maybe_object

    return curry_depends_module_object_by_uuid


def depends_active_module_object_context_curried(object_type: str) -> Callable:
    def curry_depends_active_module_object_context(
        lineage_id: int,
        module: Module = Depends(depends_active_module),
        repository: ModuleObjectContextRepository = Depends(depends_module_object_context_repository),
    ) -> ModuleObjectContextTable:
        maybe_context: Optional[ModuleObjectContextTable] = repository.get_by_ids(
            module.Module_ID,
            object_type,
            lineage_id,
        )
        if not maybe_context:
            raise HTTPException(status_code=404, detail="Module Object Context niet gevonden")
        if maybe_context.Hidden:
            raise HTTPException(status_code=404, detail="Module Object Context is verwijderd")
        return maybe_context

    return curry_depends_active_module_object_context


def depends_active_module_object_context(
    module_id: int,
    object_type: str,
    lineage_id: int,
    repository: ModuleObjectContextRepository = Depends(depends_module_object_context_repository),
) -> ModuleObjectContextTable:
    maybe_context: Optional[ModuleObjectContextTable] = repository.get_by_ids(module_id, object_type, lineage_id)
    if not maybe_context:
        raise HTTPException(status_code=404, detail="Object context niet gevonden")
    if maybe_context.Hidden:
        raise HTTPException(status_code=404, detail="Object context is verwijderd")
    return maybe_context


def depends_module_object_latest_by_id(
    module_id: int,
    object_type: str,
    lineage_id: int,
    repository: ModuleObjectRepository = Depends(depends_module_object_repository),
) -> ModuleObjectsTable:
    maybe_object: Optional[ModuleObjectsTable] = repository.get_latest_by_id(module_id, object_type, lineage_id)
    if not maybe_object:
        raise HTTPException(status_code=404, detail="Module object niet gevonden")
    return maybe_object


def depends_module_status_by_id(
    status_id: int,
    module: ModuleTable = Depends(depends_module),
    repository: ModuleStatusRepository = Depends(depends_module_status_repository),
) -> ModuleStatusHistoryTable:
    maybe_status: Optional[ModuleStatusHistoryTable] = repository.get_by_id(module.Module_ID, status_id)
    if not maybe_status:
        raise HTTPException(status_code=404, detail="Module status niet gevonden")
    return maybe_status


def depends_maybe_module_status_by_id(
    status_id: Optional[int] = None,
    module: ModuleTable = Depends(depends_module),
    repository: ModuleStatusRepository = Depends(depends_module_status_repository),
) -> Optional[ModuleStatusHistoryTable]:
    if status_id is None:
        return None
    maybe_status: Optional[ModuleStatusHistoryTable] = repository.get_by_id(module.Module_ID, status_id)
    # Giving a status_id is optional, but if you give a status_id then it must exist
    if not maybe_status:
        raise HTTPException(status_code=404, detail="Module status niet gevonden")
    return maybe_status


def depends_object_provider(
    object_repository: ObjectRepository = Depends(depends_object_repository),
    module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
) -> ObjectProvider:
    object_provider: ObjectProvider = ObjectProvider(
        object_repository,
        module_object_repository,
    )
    return object_provider


def depends_module_sorted_pagination_curried(default_column: ModuleSortColumn, default_order: SortOrder) -> Callable:
    def depends_module_sorted_pagination_inner(
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort_column: Optional[ModuleSortColumn] = None,
        sort_order: Optional[SortOrder] = None,
    ) -> ModuleSortedPagination:
        column: ModuleSortColumn = sort_column or default_column
        order: SortOrder = sort_order or default_order
        module_sort = ModuleSort(column=column, order=order)

        pagination: ModuleSortedPagination = ModuleSortedPagination(
            offset=offset,
            limit=limit,
            sort=module_sort,
        )
        return pagination

    return depends_module_sorted_pagination_inner
