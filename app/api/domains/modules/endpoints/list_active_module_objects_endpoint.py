from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.modules.repositories.module_object_repository import (
    LatestObjectPerModuleResult,
    ModuleObjectRepository,
)
from app.api.domains.modules.types import ActiveModuleObject, ModuleObjectActionFull, ModuleShort, ModuleStatusCode
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.core.tables.users import UsersTable


class ActiveModuleObjectsResponse(BaseModel):
    module: ModuleShort
    module_object: ActiveModuleObject
    action: ModuleObjectActionFull


class ListActiveModuleObjectsEndpointContext(BaseEndpointContext):
    object_type: str


@inject
async def get_list_active_module_objects_endpoint(
    lineage_id: int,
    minimum_status: Annotated[ModuleStatusCode, ModuleStatusCode.Ontwerp_PS],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    _: Annotated[UsersTable, Depends(depends_current_user)],
    context: Annotated[ListActiveModuleObjectsEndpointContext, Depends()],
) -> List[ActiveModuleObjectsResponse]:
    code = f"{context.object_type}-{lineage_id}"
    items: List[LatestObjectPerModuleResult] = module_object_repository.get_latest_per_module(
        code,
        minimum_status,
        is_active=True,
    )

    result: List[ActiveModuleObjectsResponse] = [
        ActiveModuleObjectsResponse(
            module=ModuleShort.model_validate(item.module),
            module_object=ActiveModuleObject.model_validate(item.module_object),
            action=item.context_action,
        )
        for item in items
    ]

    return result
