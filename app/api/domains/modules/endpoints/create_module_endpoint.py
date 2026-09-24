import uuid
from datetime import UTC, datetime
from typing import Annotated

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
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=3)
    module_manager_1_id: uuid.UUID
    module_manager_2_id: uuid.UUID | None = Field(None)

    @field_validator("module_manager_2_id", mode="after")
    def duplicate_manager(cls, v, info):
        if v is None:
            return v
        if "module_manager_1_id" not in info.data:
            return v
        if v == info.data["module_manager_1_id"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Duplicate manager")
        return v


class ModuleCreatedResponse(BaseModel):
    module_id: int


@inject
def post_create_module_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    object_in: ModuleCreate,
) -> ModuleCreatedResponse:
    permission_service.guard_valid_user(Permissions.module_can_create_module, user)

    timepoint: datetime = datetime.now(UTC)

    module: ModuleTable = ModuleTable(
        title=object_in.title,
        description=object_in.description,
        module_manager_1_id=object_in.module_manager_1_id,
        module_manager_2_id=object_in.module_manager_2_id,
        created_date=timepoint,
        modified_date=timepoint,
        created_by_id=user.UUID,
        modified_by_id=user.UUID,
        activated=0,
        closed=0,
        successful=0,
        temporary_locked=0,
    )

    status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
        status=ModuleStatusCodeInternal.Niet_Actief,
        created_date=timepoint,
        created_by_id=user.UUID,
    )
    module.status_history.append(status)

    session.add(module)
    session.add(status)

    session.flush()
    session.commit()

    return ModuleCreatedResponse(
        module_id=module.module_id,
    )
