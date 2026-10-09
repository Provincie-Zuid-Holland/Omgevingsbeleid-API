import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

import validators
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.services.security import Security
from app.api.domains.users.user_repository import UserRepository
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class UserCreate(BaseModel):
    name: str = Field(..., min_length=3)
    email: str
    roles: list[str]

    @field_validator("email", mode="before")
    def valid_email(cls, v):
        if not validators.email(v):
            raise ValueError("Invalid email")
        return v


class UserCreateResponse(BaseModel):
    id: uuid.UUID
    email: str
    roles: list[str]
    password: str


class CreateUserEndpointContext(BaseEndpointContext):
    allowed_roles: list[str] = Field(default_factory=list)


@inject
def post_create_user_endpoint(
    object_in: UserCreate,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[CreateUserEndpointContext, Depends()],
) -> UserCreateResponse:
    permission_service.guard_valid_user(Permissions.user_can_create_user, logged_in_user)

    if not object_in.roles:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one role is required")

    if not set(object_in.roles) <= set(context.allowed_roles):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Roles")

    same_email_user: UsersTable | None = repository.get_by_email(session, object_in.email)
    if same_email_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")

    password = "change-me-" + security.get_random_password()
    password_hashed = security.get_password_hash(password)

    user = UsersTable(
        id=uuid.uuid4(),
        name=object_in.name,
        email=object_in.email,
        roles=object_in.roles,
        is_active=True,
        password_hashed=password_hashed,
    )

    change_log: ChangeLogTable = ChangeLogTable(
        created_date=datetime.now(UTC),
        created_by_id=logged_in_user.id,
        action_type="create_user",
        action_data=object_in.model_dump_json(),
        after=json.dumps(user.to_dict_safe()),
    )

    session.add(change_log)
    session.add(user)
    session.flush()
    session.commit()

    return UserCreateResponse(
        id=user.id,
        email=user.email,
        roles=list(user.roles),
        password=password,
    )
