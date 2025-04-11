from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.services.security import Security
from app.api.domains.users.user_repository import UserRepository
from app.api.types import ResponseOK
from app.core.tables.users import UsersTable


class PasswordUpdate(BaseModel):
    password: str
    new_password: str


def post_auth_reset_password_endpoint(
    password_in: Annotated[PasswordUpdate, Depends()],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    user_repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
) -> ResponseOK:
    valid: bool = security.verify_password(password_in.password, user.Wachtwoord)
    if not valid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    user_repository.change_password(user, password_in.new_password)

    return ResponseOK(message="OK")
