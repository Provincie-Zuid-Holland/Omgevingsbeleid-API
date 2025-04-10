from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.types import ObjectCount, ObjectCountResponse
from app.api.domains.users.dependencies import depends_current_user
from app.core.tables.users import UsersTable


@inject
async def view_object_counts_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
) -> ObjectCountResponse:
    rows: List[ObjectCount] = object_repository.get_valid_counts(user.UUID)
    response = ObjectCountResponse(rows)
    return response
