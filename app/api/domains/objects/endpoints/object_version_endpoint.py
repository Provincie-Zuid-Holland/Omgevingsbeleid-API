from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.endpoint import BaseEndpointContext
from app.api.events.before_select_execution_event import BeforeSelectExecutionEvent
from app.api.events.event_manager import ApiEventManager
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.api.types import PreparedQuery
from app.core.tables.objects import ObjectsTable
from app.core.types import Model


class ObjectVersionEndpointContext(BaseEndpointContext):
    object_type: str
    response_config_model: Model


@inject
async def view_object_version_endpoint(
    object_uuid: UUID,
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    event_manager: Annotated[ApiEventManager, Depends(Provide[ApiContainer.event_manager])],
    session: Annotated[AsyncSession, Depends(depends_db_session)],
    context: Annotated[ObjectVersionEndpointContext, Depends()],
) -> BaseModel:
    prepared_query: PreparedQuery = object_repository.prepare_by_object_type_and_id(
        context.object_type,
        object_uuid,
    )
    prepare_query_event: BeforeSelectExecutionEvent = await event_manager.dispatch(
        session,
        BeforeSelectExecutionEvent.create(
            query=prepared_query.query,
            response_model=context.response_config_model,
            objects_table_ref=prepared_query.aliased_ref,
        ),
    )
    maybe_object: ObjectsTable | None = await object_repository.fetch_first(session, prepare_query_event.payload.query)
    if not maybe_object:
        raise HTTPException(status_code=404, detail="object_uuid does not exist")

    result: BaseModel = context.response_config_model.pydantic_model.model_validate(maybe_object)

    event: RetrievedObjectsEvent = await event_manager.dispatch(
        session,
        RetrievedObjectsEvent.create(
            rows=[result],
            endpoint_id=context.builder_data.endpoint_id,
            response_model=context.response_config_model,
        ),
    )
    result = event.payload.rows[0]

    return result
