from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.others.repositories.object_related_file_repository import ObjectRelatedFileRepository
from app.api.domains.others.types import ObjectRelatedFileResponse
from app.api.endpoint import BaseEndpointContext
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.others import ObjectRelatedFileTable


class ObjectRelatedFilesListEndpointContext(BaseEndpointContext):
    object_type: str


@inject
def get_object_related_files_list_endpoint(
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    object_related_file_repository: Annotated[
        ObjectRelatedFileRepository, Depends(Provide[ApiContainer.object_related_file_repository])
    ],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    context: Annotated[ObjectRelatedFilesListEndpointContext, Depends()],
) -> List[ObjectRelatedFileResponse]:
    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        session, context.object_type, lineage_id
    )
    if not object_static:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object niet gevonden")

    related_files: List[ObjectRelatedFileTable] = object_related_file_repository.get_by_object_code(
        session, object_static.Code
    )

    return [ObjectRelatedFileResponse.model_validate(rf) for rf in related_files]
