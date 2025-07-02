from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.api_container import ApiContainer
from app.api.domains.users.services.security import Security
from app.api.domains.users.types import AuthToken, UserLoginDetail
from app.api.domains.users.user_repository import UserRepository
from app.core.tables.users import UsersTable


@inject
async def post_auth_login_access_token_endpoint(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
) -> AuthToken:
    user: Optional[UsersTable] = user_repository.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    elif not user.IsActive:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive user")

    access_token: str = security.create_access_token(user.UUID)
    user_login_detail: UserLoginDetail = UserLoginDetail.model_validate(user)

    response: AuthToken = AuthToken.model_validate({
        "access_token": access_token,
        "token_type": "bearer",
        "identifier": user_login_detail,
    })
    return response
