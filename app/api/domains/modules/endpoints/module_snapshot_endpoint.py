from typing import Annotated, Any, Dict, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_module, depends_module_status_by_id
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.modules import ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable
from app.core.utils.utils import table_to_dict


class ModuleSnapshot(BaseModel):
    Objects: List[Dict[str, Any]]


@inject
def get_module_snapshot_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_module)],
    status: Annotated[ModuleStatusHistoryTable, Depends(depends_module_status_by_id)],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
) -> ModuleSnapshot:
    module_objects: List[ModuleObjectsTable] = module_object_repository.get_objects_in_time(
        module.Module_ID,
        status.Created_Date,
    )
    dict_objects: List[dict] = [table_to_dict(t) for t in module_objects]

    response = ModuleSnapshot(
        Objects=dict_objects,
    )
    return response
