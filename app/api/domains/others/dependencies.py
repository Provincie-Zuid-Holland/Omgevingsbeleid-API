import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import StorageFileTable


@inject
def depends_object_by_uuid(
    uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
):
    maybe_object: Optional[ObjectsTable] = repository.get_by_uuid(session, uuid)
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object niet gevonden")
    return maybe_object


@inject
def depends_storage_file(
    file_uuid: uuid.UUID,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
):
    maybe_file: Optional[StorageFileTable] = repository.get_by_uuid(session, file_uuid)
    if not maybe_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Storage file niet gevonden")
    return maybe_file
