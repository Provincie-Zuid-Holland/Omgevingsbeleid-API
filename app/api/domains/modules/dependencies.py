from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.api.domains.modules.repositories.module_repository import ModuleRepository
from app.core.tables.modules import ModuleTable


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
