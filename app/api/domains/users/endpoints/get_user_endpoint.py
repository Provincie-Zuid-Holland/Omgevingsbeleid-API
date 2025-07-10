import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.users.types import User
from app.api.domains.users.user_repository import UserRepository
from app.core.tables.users import UsersTable


@inject
def view_get_user_endpoint(
    user_uuid: uuid.UUID,
    logged_in_user: Annotated[UsersTable, Depends(depends_current_user)],
    repository: Annotated[UserRepository, Depends(Provide[ApiContainer.user_repository])],
) -> User:
    db_user: Optional[UsersTable] = repository.get_by_uuid(user_uuid)
    if not db_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User does not exist")

    user: User = User.model_validate(db_user)
    return user
