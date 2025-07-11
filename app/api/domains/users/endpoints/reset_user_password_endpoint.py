import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.services.security import Security
from app.api.domains.users.user_repository import UserRepository
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class ResetPasswordResponse(BaseModel):
    UUID: uuid.UUID
    NewPassword: str


@inject
def post_reset_user_password_endpoint(
    user_uuid: uuid.UUID,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResetPasswordResponse:
    permission_service.guard_valid_user(Permissions.user_can_reset_user_password, logged_in_user)

    user: Optional[UsersTable] = repository.get_by_uuid(session, user_uuid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist")
    if not user.IsActive:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is inactive")

    password = "change-me-" + security.get_random_password()
    password_hash = security.get_password_hash(password)

    user.Wachtwoord = password_hash

    change_log = ChangeLogTable(
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=logged_in_user.UUID,
        Action_Type="reset_user_password",
        Action_Data=json.dumps({"UUID": str(user.UUID)}),
    )

    session.add(change_log)
    session.add(user)
    session.flush()
    session.commit()

    return ResetPasswordResponse(
        UUID=user.UUID,
        NewPassword=password,
    )
