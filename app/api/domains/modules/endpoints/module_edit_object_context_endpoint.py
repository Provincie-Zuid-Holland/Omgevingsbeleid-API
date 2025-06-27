import json
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context,
    depends_module_object_latest_by_id,
)
from app.api.domains.modules.types import ModuleObjectAction
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class ModuleEditObjectContext(BaseModel):
    Action: Optional[ModuleObjectAction] = None
    Explanation: Optional[str] = None
    Conclusion: Optional[str] = None
    model_config = ConfigDict(use_enum_values=True)


@inject
async def post_module_edit_object_context_endpoint(
    object_in: Annotated[ModuleEditObjectContext, Depends()],
    _: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module_object: Annotated[ModuleObjectsTable, Depends(depends_module_object_latest_by_id)],
    object_context: Annotated[ModuleObjectContextTable, Depends(depends_active_module_object_context)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_edit_module_object_context,
        user,
        whitelisted_uuids=[
            module_object.ObjectStatics.Owner_1_UUID,
            module_object.ObjectStatics.Owner_2_UUID,
            module_object.ObjectStatics.Portfolio_Holder_1_UUID,
            module_object.ObjectStatics.Portfolio_Holder_2_UUID,
            module_object.ObjectStatics.Client_1_UUID,
        ],
    )

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    log_before: str = json.dumps(object_context.to_dict())

    for key, value in changes.items():
        setattr(object_context, key, value)

    timepoint: datetime = datetime.now(timezone.utc)

    object_context.Modified_By_UUID = user.UUID
    object_context.Modified_Date = timepoint

    db.add(object_context)

    change_log = ChangeLogTable(
        Object_Type=object_context.Object_Type,
        Object_ID=object_context.Object_ID,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Action_Type="module_edit_object_context",
        Action_Data=object_in.model_dump_json(),
        Before=log_before,
        After=json.dumps(object_context.to_dict()),
    )
    db.add(change_log)

    db.flush()
    db.commit()

    return ResponseOK(message="OK")
