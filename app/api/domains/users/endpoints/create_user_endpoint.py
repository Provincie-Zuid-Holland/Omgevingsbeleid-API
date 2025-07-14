import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

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
from app.core.tables.users import IS_ACTIVE, UsersTable


class UserCreate(BaseModel):
    Gebruikersnaam: str = Field(..., min_length=3)
    Email: str
    Rol: str

    @field_validator("Email", mode="before")
    def valid_email(cls, v):
        if not validators.email(v):
            raise ValueError("Invalid email")
        return v


class UserCreateResponse(BaseModel):
    UUID: uuid.UUID
    Email: str
    Rol: str
    Password: str


class CreateUserEndpointContext(BaseEndpointContext):
    allowed_roles: List[str] = Field(default_factory=list)


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

    if object_in.Rol not in context.allowed_roles:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Rol")

    same_email_user: Optional[UsersTable] = repository.get_by_email(session, object_in.Email)
    if same_email_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already in use")

    password = "change-me-" + security.get_random_password()
    password_hash = security.get_password_hash(password)

    user = UsersTable(
        UUID=uuid.uuid4(),
        Gebruikersnaam=object_in.Gebruikersnaam,
        Email=object_in.Email,
        Rol=object_in.Rol,
        Status=IS_ACTIVE,
        Wachtwoord=password_hash,
    )

    change_log = ChangeLogTable(
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=logged_in_user.UUID,
        Action_Type="create_user",
        Action_Data=object_in.model_dump_json(),
        After=json.dumps(user.to_dict_safe()),
    )

    session.add(change_log)
    session.add(user)
    session.flush()
    session.commit()

    return UserCreateResponse(
        UUID=user.UUID,
        Email=user.Email,
        Rol=user.Rol or "",
        Password=password,
    )
