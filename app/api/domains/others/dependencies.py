import uuid
from typing import Annotated, Optional

from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.core.tables.objects import ObjectsTable


def depends_object_by_uuid(
    uuid: uuid.UUID,
    repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
):
    maybe_object: Optional[ObjectsTable] = repository.get_by_uuid(uuid)
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object niet gevonden")
    return maybe_object
