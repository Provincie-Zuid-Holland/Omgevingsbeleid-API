from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from pydantic import BaseModel

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import ModuleStatusCode
from app.api.endpoint import BaseEndpointContext
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleTable
from app.core.types import Model


class ModuleObjectVersionEndpointContext(BaseEndpointContext):
    object_type: str
    endpoint_id: str
    minimum_status: Optional[ModuleStatusCode] = None
    response_config_model: Model


@inject
async def view_module_object_version_endpoint(
    lineage_id: Annotated[int, Depends()],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    context: Annotated[ModuleObjectVersionEndpointContext, Depends()],
) -> BaseModel: ...
