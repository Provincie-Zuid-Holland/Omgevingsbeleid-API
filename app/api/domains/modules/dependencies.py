from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.repositories.module_object_context_repository import ModuleObjectContextRepository
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.api.domains.modules.repositories.module_status_repository import ModuleStatusRepository
from app.api.domains.modules.types import ModuleSortColumn
from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SortOrder
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable


@inject
def depends_module(
    module_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    module_repository: Annotated[ModuleRepository, Depends(Provide[ApiContainer.module_repository])],
) -> ModuleTable:
    maybe_module: Optional[ModuleTable] = module_repository.get_by_id(session, module_id)
    if not maybe_module:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module niet gevonden")
    return maybe_module


def depends_active_module(
    module: Annotated[ModuleTable, Depends(depends_module)],
) -> ModuleTable:
    if module.Closed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "De module is gesloten")
    return module


def depends_active_and_activated_module(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
) -> ModuleTable:
    if not module.Activated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "De module is nog niet actief")
    return module


@inject
def depends_module_object_latest_by_id(
    module_id: int,
    object_type: str,
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])],
) -> ModuleObjectsTable:
    maybe_object: Optional[ModuleObjectsTable] = repository.get_latest_by_id(
        session, module_id, object_type, lineage_id
    )
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module object niet gevonden")
    return maybe_object


@inject
def depends_active_module_object_context(
    module_id: int,
    object_type: str,
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[
        ModuleObjectContextRepository, Depends(Provide[ApiContainer.module_object_context_repository])
    ],
) -> ModuleObjectContextTable:
    maybe_context: Optional[ModuleObjectContextTable] = repository.get_by_ids(
        session, module_id, object_type, lineage_id
    )
    if not maybe_context:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object context niet gevonden")
    if maybe_context.Hidden:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object context is verwijderd")
    return maybe_context


@inject
def depends_module_status_by_id(
    status_id: int,
    module: Annotated[ModuleTable, Depends(depends_module)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[ModuleStatusRepository, Depends(Provide[ApiContainer.module_status_repository])],
) -> ModuleStatusHistoryTable:
    maybe_status: Optional[ModuleStatusHistoryTable] = repository.get_by_id(session, module.Module_ID, status_id)
    if not maybe_status:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module status niet gevonden")
    return maybe_status


def depends_optional_module_sorted_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort_column: Optional[ModuleSortColumn] = None,
    sort_order: Optional[SortOrder] = None,
) -> OptionalSortedPagination:
    optional_sort = OptionalSort(
        column=sort_column.value if sort_column else None,
        order=sort_order,
    )
    pagination = OptionalSortedPagination(
        offset=offset,
        limit=limit,
        sort=optional_sort,
    )
    return pagination
