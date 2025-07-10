import uuid
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import ModuleStatusCode
from app.api.domains.users.dependencies import depends_optional_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable
from app.core.types import Model


class ModuleObjectVersionEndpointContext(BaseEndpointContext):
    object_type: str
    minimum_status: Optional[ModuleStatusCode] = None
    response_config_model: Model
    require_auth: bool


@inject
def view_module_object_version_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    user: Annotated[Optional[UsersTable], Depends(depends_optional_current_user)],
    context: Annotated[ModuleObjectVersionEndpointContext, Depends()],
    object_uuid: uuid.UUID,
) -> BaseModel:
    if context.require_auth:
        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    if not user and context.minimum_status:
        if module.Current_Status not in ModuleStatusCode.after(context.minimum_status):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "module objects lacks the minimum status for view.")

    module_object: Optional[ModuleObjectsTable] = module_object_repository.get_by_module_id_object_type_and_uuid(
        module.Module_ID,
        context.object_type,
        object_uuid,
    )
    if not module_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module Object niet gevonden")

    object_context: ModuleObjectContextTable = module_object.ModuleObjectContext
    if object_context.Hidden:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module Object Context is verwijderd")

    row: BaseModel = context.response_config_model.pydantic_model.model_validate(module_object)
    rows: List[BaseModel] = [row]

    # Ask extensions for more information
    event: RetrievedModuleObjectsEvent = event_manager.dispatch(
        RetrievedModuleObjectsEvent.create(
            rows,
            context.builder_data.endpoint_id,
            context.response_config_model,
        )
    )
    rows = event.payload.rows

    return rows[0]
