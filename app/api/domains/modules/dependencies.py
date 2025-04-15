from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.api.domains.modules.repositories.module_object_context_repository import ModuleObjectContextRepository
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable


@inject
def depends_module(
    module_id: int,
    module_repository: Annotated[ModuleRepository, Depends(Provide[ApiContainer.module_repository])],
) -> ModuleTable:
    maybe_module: Optional[ModuleTable] = module_repository.get_by_id(module_id)
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
    repository: Annotated[ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])],
) -> ModuleObjectsTable:
    maybe_object: Optional[ModuleObjectsTable] = repository.get_latest_by_id(module_id, object_type, lineage_id)
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module object niet gevonden")
    return maybe_object


@inject
def depends_active_module_object_context(
    module_id: int,
    object_type: str,
    lineage_id: int,
    repository: Annotated[
        ModuleObjectContextRepository, Depends(Provide[ApiContainer.module_object_context_repository])
    ],
) -> ModuleObjectContextTable:
    maybe_context: Optional[ModuleObjectContextTable] = repository.get_by_ids(module_id, object_type, lineage_id)
    if not maybe_context:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object context niet gevonden")
    if maybe_context.Hidden:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object context is verwijderd")
    return maybe_context
