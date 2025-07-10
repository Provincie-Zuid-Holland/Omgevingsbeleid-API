# from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.events.module_object_patched_event import ModuleObjectPatchedEvent
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.services.event.event_manager import EventManager
from app.core.tables.modules import ModuleTable
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.tables.users import UsersTable
from app.core.types import Model


class ModulePatchObjectContext(BaseEndpointContext):
    object_type: str
    request_config_model: Model
    response_config_model: Model


@inject
def post_module_patch_object_endpoint(
    lineage_id: int,
    object_in: Annotated[BaseModel, Depends()],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    context: Annotated[ModulePatchObjectContext, Depends()],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    event_manager: Annotated[EventManager, Depends(Provide[ApiContainer.event_manager])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
) -> BaseModel:
    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        context.object_type,
        lineage_id,
    )
    if not object_static:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object static niet gevonden")

    permission_service.guard_valid_user(
        Permissions.module_can_patch_object_in_module,
        user,
        [object_static.Owner_1_UUID, object_static.Owner_2_UUID],
    )
    guard_module_not_locked(module)

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    timepoint: datetime = datetime.now(timezone.utc)
    old_record, new_record = module_object_repository.patch_latest_module_object(
        module.Module_ID,
        context.object_type,
        lineage_id,
        changes,
        timepoint,
        user.UUID,
    )

    event: ModuleObjectPatchedEvent = event_manager.dispatch(
        ModuleObjectPatchedEvent.create(
            user,
            changes,
            timepoint,
            context.response_config_model,
            old_record,
            new_record,
        )
    )
    new_record = event.payload.new_record

    # cache statics title if needed
    if "Title" in changes:
        valid_version = db.query(ObjectsTable).filter(ObjectsTable.Code == new_record.Code).first()
        if valid_version is None:
            object_static.Cached_Title = changes["Title"]
            db.add(object_static)

    db.add(new_record)
    db.flush()
    db.commit()

    response: BaseModel = context.response_config_model.model_validate(new_record)
    return response
