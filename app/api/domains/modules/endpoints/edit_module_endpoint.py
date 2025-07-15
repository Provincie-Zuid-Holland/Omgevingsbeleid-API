import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleTable
from app.core.tables.users import UsersTable


class ModuleEdit(BaseModel):
    Temporary_Locked: Optional[bool] = Field(None)

    Title: Optional[str] = Field(None, min_length=3)
    Description: Optional[str] = Field(None, min_length=3)
    Module_Manager_1_UUID: Optional[uuid.UUID] = Field(None)
    Module_Manager_2_UUID: Optional[uuid.UUID] = Field(None)

    @field_validator("Module_Manager_2_UUID", mode="after")
    def duplicate_manager(cls, v, info):
        if v is None:
            return v
        if "Module_Manager_1_UUID" not in info.data:
            return v
        if v == info.data["Module_Manager_1_UUID"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Duplicate manager")
        return v


@inject
def post_edit_module_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    object_in: ModuleEdit,
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_edit_module,
        user,
        [module.Module_Manager_1_UUID, module.Module_Manager_2_UUID],
    )

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(module, key, value)

    module.Modified_By_UUID = user.UUID
    module.Modified_Date = datetime.now(timezone.utc)

    session.add(module)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
