from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.repositories.module_object_repository import (
    LatestObjectPerModuleResult,
    ModuleObjectRepository,
)
from app.api.domains.modules.types import ActiveModuleObject, ModuleObjectActionFull, ModuleShort, ModuleStatusCode
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.core.tables.users import UsersTable


class ActiveModuleObjectsResponse(BaseModel):
    Module: ModuleShort
    Module_Object: ActiveModuleObject
    Action: ModuleObjectActionFull


class ListActiveModuleObjectsEndpointContext(BaseEndpointContext):
    object_type: str


@inject
def get_list_active_module_objects_endpoint(
    lineage_id: int,
    minimum_status: Annotated[ModuleStatusCode, ModuleStatusCode.Ontwerp_PS],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    _: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[ListActiveModuleObjectsEndpointContext, Depends()],
) -> List[ActiveModuleObjectsResponse]:
    code = f"{context.object_type}-{lineage_id}"
    items: List[LatestObjectPerModuleResult] = module_object_repository.get_latest_per_module(
        session,
        code,
        minimum_status,
        is_active=True,
    )

    result: List[ActiveModuleObjectsResponse] = [
        ActiveModuleObjectsResponse(
            Module=ModuleShort.model_validate(item.module),
            Module_Object=ActiveModuleObject.model_validate(item.module_object),
            Action=item.context_action,
        )
        for item in items
    ]

    return result
