from typing import Annotated, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.others.repositories.object_related_file_repository import ObjectRelatedFileRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.others import ObjectRelatedFileTable
from app.core.tables.users import UsersTable


@inject
def post_object_related_files_delete_endpoint(
    related_file_uuid: UUID,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    object_related_file_repository: Annotated[
        ObjectRelatedFileRepository, Depends(Provide[ApiContainer.object_related_file_repository])
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> ResponseOK:
    maybe_file: Optional[ObjectRelatedFileTable] = object_related_file_repository.get_by_uuid(
        session, related_file_uuid
    )
    if not maybe_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bestand niet gevonden")

    permission_service.guard_valid_user(
        Permissions.can_delete_object_related_file,
        user,
        [
            maybe_file.ObjectStatics.Owner_1_UUID,
            maybe_file.ObjectStatics.Owner_2_UUID,
        ],
    )

    session.delete(maybe_file)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
