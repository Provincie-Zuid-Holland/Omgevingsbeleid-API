import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

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
    temporary_locked: bool | None = Field(None)

    title: str | None = Field(None, min_length=3)
    description: str | None = Field(None, min_length=3)
    module_manager_1_id: uuid.UUID | None = Field(None)
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
        [module.module_manager_1_id, module.module_manager_2_id],
    )

    changes: dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    for key, value in changes.items():
        setattr(module, key, value)

    module.modified_by_id = user.UUID
    module.modified_date = datetime.now(UTC)

    session.add(module)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
