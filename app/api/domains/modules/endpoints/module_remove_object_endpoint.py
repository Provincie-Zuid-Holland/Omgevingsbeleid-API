from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module, depends_active_module_object_context
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.objects.dependencies import depends_object_static_by_object_type_and_id
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleObjectContextTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable


@inject
def post_module_remove_object_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    object_context: Annotated[ModuleObjectContextTable, Depends(depends_active_module_object_context)],
    object_static: Annotated[
        ObjectStaticsTable,
        Depends(
            depends_object_static_by_object_type_and_id,
        ),
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_remove_object_from_module,
        user,
        whitelisted_uuids=[
            module.Module_Manager_1_UUID,
            module.Module_Manager_2_UUID,
        ],
    )
    guard_module_not_locked(module)

    timepoint: datetime = datetime.now(timezone.utc)
    object_context.Hidden = True
    object_context.Modified_By_UUID = user.UUID
    object_context.Modified_Date = timepoint
    db.add(object_context)

    _, new_record = module_object_repository.patch_latest_module_object(
        object_context.Module_ID,
        object_context.Object_Type,
        object_context.Object_ID,
        {
            "Deleted": True,
        },
        timepoint,
        user.UUID,
    )
    db.add(new_record)
    db.flush()
    db.commit()

    return ResponseOK(message="OK")
