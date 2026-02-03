from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable
from app.core.types import Model


class ModuleObjectLatestEndpointContext(BaseEndpointContext):
    object_type: str
    response_config_model: Model


@inject
def view_module_object_latest_endpoint(
    lineage_id: int,
    _: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_module)],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[ModuleObjectLatestEndpointContext, Depends()],
) -> BaseModel:
    module_object: Optional[ModuleObjectsTable] = module_object_repository.get_latest_by_id(
        session,
        module.Module_ID,
        context.object_type,
        lineage_id,
    )
    if not module_object:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "lineage_id does not exist")

    row: BaseModel = context.response_config_model.pydantic_model.model_validate(module_object)

    event: RetrievedModuleObjectsEvent = event_manager.dispatch(
        session,
        RetrievedModuleObjectsEvent.create(
            [row],
            context.builder_data.endpoint_id,
            context.response_config_model,
        ),
    )
    row = event.payload.rows[0]

    return row
