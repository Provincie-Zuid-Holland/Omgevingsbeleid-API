from typing import Annotated, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.api_container import ApiContainer
from app.api.domains.users.services.security import Security
from app.api.domains.users.types import TokenPayload
from app.api.domains.users.user_repository import UserRepository
from app.core.tables.users import UsersTable

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token", auto_error=False)


@inject
def depends_current_user(
    token: Annotated[Optional[str], Depends(reusable_oauth2)],
    user_repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
) -> UsersTable:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    token_data: TokenPayload = security.decode_token(token)

    user: Optional[UsersTable] = user_repository.get_by_uuid(UUID(token_data.sub))
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Token valid, but no matching user found.")
    if not user.IsActive:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive user")

    return user


@inject
def depends_optional_current_user(
    token: Annotated[Optional[str], Depends(reusable_oauth2)],
    user_repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
) -> Optional[UsersTable]:
    try:
        return depends_current_user(token, user_repository, security)
    except HTTPException:
        return None
