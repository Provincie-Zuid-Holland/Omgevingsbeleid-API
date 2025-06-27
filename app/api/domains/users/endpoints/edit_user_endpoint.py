import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

import validators
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.user_repository import UserRepository
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import IS_ACTIVE, UsersTable


class EditUser(BaseModel):
    Gebruikersnaam: Optional[str] = Field(None)
    Email: Optional[str] = Field(None)
    Rol: Optional[str] = Field(None)
    IsActive: Optional[bool] = Field(None)


class EditUserEndpointContext(BaseEndpointContext):
    allowed_roles: List[str] = Field(default_factory=list)


@inject
async def post_edit_user_endpoint(
    user_uuid: uuid.UUID,
    object_in: EditUser,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[EditUserEndpointContext, Depends()],
) -> ResponseOK:
    permission_service.guard_valid_user(Permissions.user_can_edit_user, logged_in_user)

    changes: dict = object_in.dict(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    user: Optional[UsersTable] = repository.get_by_uuid(user_uuid)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User does not exist")

    if object_in.Email:
        same_email_user: Optional[UsersTable] = repository.get_by_email(object_in.Email)
        if same_email_user and same_email_user.UUID != user.UUID:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")

    user_before_dict: dict = user.to_dict_safe()
    log_before: str = json.dumps(user_before_dict)

    # We handle IsActive separately as that is not really a column
    handle_is_active: Optional[bool] = changes.pop("IsActive", None)
    if handle_is_active == True:
        user.Status = IS_ACTIVE
    elif handle_is_active == False:
        user.Status = ""

    for key, value in changes.items():
        setattr(user, key, value)

    if not validators.email(user.Email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email")
    if user.Rol not in context.allowed_roles:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Rol")

    user_after_dict: dict = user.to_dict_safe()

    change_log: ChangeLogTable = ChangeLogTable(
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=logged_in_user.UUID,
        Action_Type="edit_user",
        Action_Data=object_in.model_dump_json(),
        Before=log_before,
        After=json.dumps(user_after_dict),
    )

    db.add(change_log)
    db.add(user)
    db.flush()
    db.commit()

    return ResponseOK(message="OK")
