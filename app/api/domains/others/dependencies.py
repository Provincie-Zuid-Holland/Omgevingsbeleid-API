import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.api.domains.others.repositories.storage_file_repository import StorageFileRepository
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import HoofdlijnTable, StorageFileTable


@inject
async def depends_object_by_uuid(
    uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
):
    maybe_object: ObjectsTable | None = await repository.get_by_id(session, uuid)
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object niet gevonden")
    return maybe_object


@inject
async def depends_storage_file(
    file_uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
):
    maybe_file: StorageFileTable | None = await repository.get_by_id(session, file_uuid)
    if not maybe_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Storage file niet gevonden")
    return maybe_file


@inject
async def depends_storage_file_with_binary(
    file_uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    repository: Annotated[StorageFileRepository, Depends(Provide[ApiContainer.storage_file_repository])],
):
    maybe_file: StorageFileTable | None = await repository.get_with_binary(session, file_uuid)
    if not maybe_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Storage file niet gevonden")
    return maybe_file


@inject
async def depends_hoofdlijn(
    hoofdlijn_uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    repository: Annotated[HoofdlijnRepository, Depends(Provide[ApiContainer.hoofdlijn_repository])],
):
    maybe_hoofdlijn: HoofdlijnTable | None = await repository.get_by_id(session, hoofdlijn_uuid)
    if not maybe_hoofdlijn:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hoofdlijn niet gevonden")
    return maybe_hoofdlijn
