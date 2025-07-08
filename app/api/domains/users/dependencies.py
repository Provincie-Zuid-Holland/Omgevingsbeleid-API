from typing import Annotated, Callable, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.api_container import ApiContainer
from app.api.domains.users.services.security import Security
from app.api.domains.users.types import TokenPayload
from app.api.domains.users.user_repository import UserRepository
from app.api.services.permission_service import PermissionService
from app.core.tables.users import UsersTable

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token", auto_error=False)


@inject
def depends_current_user(
    token: Annotated[Optional[str], Depends(reusable_oauth2)],
    user_repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
    security: Annotated[Security, Depends(Provide[ApiContainer.security])],
) -> UsersTable:
    return _do_depends_current_user(token, user_repository, security)


def _do_depends_current_user(
    token: Optional[str],
    user_repository: UserRepository,
    security: Security,
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
        return _do_depends_current_user(token, user_repository, security)
    except HTTPException:
        return None


def depends_current_user_with_permission_curried(
    required_permission: str,
) -> Callable:
    @inject
    def depends_active_user_with_permission(
        current_user: Annotated[UsersTable, Depends(depends_current_user)],
        permission: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    ):
        if not permission.has_permission(required_permission, current_user):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user role")
        return current_user

    return depends_active_user_with_permission
