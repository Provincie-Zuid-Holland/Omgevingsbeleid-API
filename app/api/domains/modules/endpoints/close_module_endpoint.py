from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.types import ModuleStatusCodeInternal
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable


@inject
async def post_close_module_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_close_module,
        user,
        [module.Module_Manager_1_UUID, module.Module_Manager_2_UUID],
    )

    timepoint: datetime = datetime.now(timezone.utc)

    module.Closed = True
    module.Modified_By_UUID = user.UUID
    module.Modified_Date = timepoint
    db.add(module)

    status = ModuleStatusHistoryTable(
        Module_ID=module.Module_ID,
        Status=ModuleStatusCodeInternal.Gesloten,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
    )
    db.add(status)

    db.flush()
    db.commit()

    return ResponseOK(message="OK")
