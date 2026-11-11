import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.create_user_service import CreateUserService
from app.api.services.permission_service import PermissionService
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class UserCreate(BaseModel):
    name: str = Field(..., min_length=3)
    email: str
    roles: list[str]


class UserCreateResponse(BaseModel):
    id: uuid.UUID
    email: str
    roles: list[str]
    password: str


class CreateUserEndpointContext(BaseEndpointContext):
    allowed_roles: list[str] = Field(default_factory=list)


@inject
async def post_create_user_endpoint(
    object_in: UserCreate,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    user_service: Annotated[CreateUserService, Depends(Provide[ApiContainer.create_user_service])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[CreateUserEndpointContext, Depends()],
) -> UserCreateResponse:
    permission_service.guard_valid_user(Permissions.user_can_create_user, logged_in_user)

    password: str = user_service.generate_password()

    try:
        user: UsersTable = await user_service.create_user(
            session,
            object_in.name,
            object_in.email,
            password,
            set(object_in.roles),
            set(context.allowed_roles),
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))

    change_log: ChangeLogTable = ChangeLogTable(
        created_date=datetime.now(UTC),
        created_by_id=logged_in_user.id,
        action_type="create_user",
        action_data=object_in.model_dump_json(),
        after=json.dumps(user.to_dict_safe()),
    )

    session.add(change_log)
    await session.flush()
    await session.commit()

    return UserCreateResponse(
        id=user.id,
        email=user.email,
        roles=list(user.roles),
        password=password,
    )
