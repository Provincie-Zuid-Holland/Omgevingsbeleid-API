from typing import Annotated, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.endpoint import BaseEndpointContext
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.event_manager import EventManager
from app.core.tables.objects import ObjectsTable
from app.core.types import Model


class ObjectVersionEndpointContext(BaseEndpointContext):
    object_type: str
    response_config_model: Model


@inject
async def view_object_version_endpoint(
    object_uuid: UUID,
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    context: Annotated[ObjectVersionEndpointContext, Depends()],
) -> BaseModel:
    maybe_object: Optional[ObjectsTable] = object_repository.get_by_object_type_and_uuid(
        context.object_type,
        object_uuid,
    )
    if not maybe_object:
        raise HTTPException(status_code=404, detail="object_uuid does not exist")

    result: BaseModel = context.response_config_model.pydantic_model.model_validate(maybe_object)

    event: RetrievedObjectsEvent = event_manager.dispatch(
        RetrievedObjectsEvent.create(
            rows=[result],
            endpoint_id=context.builder_data.endpoint_id,
            response_model=context.response_config_model,
        )
    )
    result = event.payload.rows[0]

    return result
