from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.endpoint import BaseEndpointContext
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.api.events.event_manager import ApiEventManager
from app.core.tables.objects import ObjectStaticsTable
from app.core.types import Model


class ObjectStaticEndpointContext(BaseEndpointContext):
    object_type: str
    response_config_model: Model


@inject
def view_get_object_static_endpoint(
    lineage_id: int,
    repository: Annotated[ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])],
    event_manager: Annotated[ApiEventManager, Depends(Provide[ApiContainer.event_manager])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[ObjectStaticEndpointContext, Depends()],
) -> BaseModel:
    maybe_static: Optional[ObjectStaticsTable] = repository.get_by_object_type_and_id(
        session,
        context.object_type,
        lineage_id,
    )
    if not maybe_static:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object static niet gevonden")

    result: BaseModel = context.response_config_model.pydantic_model.model_validate(maybe_static)
    event: RetrievedObjectsEvent = event_manager.dispatch(
        session,
        RetrievedObjectsEvent.create(
            rows=[result],
            endpoint_id=context.builder_data.endpoint_id,
            response_model=context.response_config_model,
        ),
    )
    result = event.payload.rows[0]

    return result
