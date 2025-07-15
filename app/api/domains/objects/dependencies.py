from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.objects.types import FilterObjectCode
from app.core.tables.objects import ObjectStaticsTable


def depends_filter_object_code(
    object_type: Optional[str] = None,
    lineage_id: Optional[int] = None,
) -> Optional[FilterObjectCode]:
    if object_type is None and lineage_id is None:
        return None

    if object_type is None or lineage_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "object_type and object_lineage_id should be supplied together."
        )

    return FilterObjectCode(
        object_type=object_type,
        lineage_id=lineage_id,
    )


@inject
def depends_object_static_by_object_type_and_id(
    object_type: str,
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    repository: Annotated[ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])],
):
    maybe_static: Optional[ObjectStaticsTable] = repository.get_by_object_type_and_id(
        session,
        object_type,
        lineage_id,
    )
    if not maybe_static:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object static niet gevonden")
    return maybe_static
