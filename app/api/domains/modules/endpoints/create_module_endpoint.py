import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.types import ModuleStatusCodeInternal
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable
from app.core.tables.users import UsersTable


class ModuleCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str = Field(..., min_length=3)
    Module_Manager_1_UUID: uuid.UUID
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


class ModuleCreatedResponse(BaseModel):
    Module_ID: int


@inject
def post_create_module_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    object_in: ModuleCreate,
) -> ModuleCreatedResponse:
    permission_service.guard_valid_user(Permissions.module_can_close_module, user)

    timepoint: datetime = datetime.now(timezone.utc)

    module: ModuleTable = ModuleTable(
        Title=object_in.Title,
        Description=object_in.Description,
        Module_Manager_1_UUID=object_in.Module_Manager_1_UUID,
        Module_Manager_2_UUID=object_in.Module_Manager_2_UUID,
        Created_Date=timepoint,
        Modified_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_By_UUID=user.UUID,
        Activated=0,
        Closed=0,
        Successful=0,
        Temporary_Locked=0,
    )

    status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
        Status=ModuleStatusCodeInternal.Niet_Actief,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
    )
    module.status_history.append(status)

    session.add(module)
    session.add(status)

    session.flush()
    session.commit()

    return ModuleCreatedResponse(
        Module_ID=module.Module_ID,
    )
