from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_and_activated_module
from app.api.domains.modules.types import ModuleStatusCode
from app.api.domains.modules.utils import guard_module_is_locked
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable


class ModulePatchStatus(BaseModel):
    Status: ModuleStatusCode
    model_config = ConfigDict(use_enum_values=True)


@inject
def post_module_patch_status_endpoint(
    object_in: ModulePatchStatus,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_active_and_activated_module)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_patch_module_status,
        user,
        whitelisted_uuids=[
            module.Module_Manager_1_UUID,
            module.Module_Manager_2_UUID,
        ],
    )
    guard_module_is_locked(module)

    status = ModuleStatusHistoryTable(
        Module_ID=module.Module_ID,
        Status=object_in.Status,
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=user.UUID,
    )
    db.add(status)
    db.flush()
    db.commit()

    return ResponseOK(message="OK")
