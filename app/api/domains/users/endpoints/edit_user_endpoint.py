import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

import validators
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.user_repository import UserRepository
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class EditUser(BaseModel):
    name: str | None = Field(None)
    email: str | None = Field(None)
    roles: list[str] | None = Field(None)
    is_active: bool | None = Field(None)


class EditUserEndpointContext(BaseEndpointContext):
    allowed_roles: list[str] = Field(default_factory=list)


@inject
def post_edit_user_endpoint(
    user_uuid: uuid.UUID,
    object_in: EditUser,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[EditUserEndpointContext, Depends()],
) -> ResponseOK:
    permission_service.guard_valid_user(Permissions.user_can_edit_user, logged_in_user)

    changes: dict = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    user: UsersTable | None = repository.get_by_uuid(session, user_uuid)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User does not exist")

    if object_in.email:
        same_email_user: UsersTable | None = repository.get_by_email(session, object_in.email)
        if same_email_user and same_email_user.id != user.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")

    user_before_dict: dict = user.to_dict_safe()
    log_before: str = json.dumps(user_before_dict)

    for key, value in changes.items():
        setattr(user, key, value)

    if not user.roles:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one role is required")

    if not validators.email(user.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid email")
    if not set(user.roles) <= set(context.allowed_roles):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Roles")

    user_after_dict: dict = user.to_dict_safe()

    change_log: ChangeLogTable = ChangeLogTable(
        created_date=datetime.now(UTC),
        created_by_id=logged_in_user.id,
        action_type="edit_user",
        action_data=object_in.model_dump_json(),
        before=log_before,
        after=json.dumps(user_after_dict),
    )

    session.add(change_log)
    session.add(user)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
