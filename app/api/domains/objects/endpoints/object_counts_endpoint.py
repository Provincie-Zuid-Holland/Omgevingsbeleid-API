from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectCount, ObjectCountResponse
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.users import UsersTable


@inject
def view_object_counts_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
) -> ObjectCountResponse:
    rows: List[ObjectCount] = object_repository.get_valid_counts(session, user.UUID)
    response = ObjectCountResponse(rows)
    return response
