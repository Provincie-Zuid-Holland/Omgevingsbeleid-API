# from datetime import datetime, timezone
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.events.module_object_patched_event import ModuleObjectPatchedEvent
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.events.event_manager import ApiEventManager
from app.core.services.main_config import MainConfig
from app.core.tables.modules import ModuleTable
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.tables.users import UsersTable
from app.core.types import Model


class TargetCodesModuleOrValidRuleConfig(BaseModel):
    object_types: List[str]


def _guard_target_codes_in_module_or_valid(
    session: Session,
    object_repository: ObjectRepository,
    module_object_repository: ModuleObjectRepository,
    module_id: int,
    target_codes: List[str],
) -> None:
    codes = set(target_codes)
    valid_codes = object_repository.get_valid_codes(session, codes)

    remaining_codes = codes - valid_codes
    module_objects = module_object_repository.get_latest_by_module_id_object_codes(session, module_id, remaining_codes)

    invalid_codes = [
        code
        for code in target_codes
        if code not in valid_codes and (code not in module_objects or module_objects[code].Deleted)
    ]

    if invalid_codes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Gebied/gebiedengroep {', '.join(invalid_codes)} is niet vigerend en zit niet in deze module",
        )


class ModulePatchObjectContext(BaseEndpointContext):
    object_type: str
    request_config_model: Model
    response_config_model: Model


@inject
def post_module_patch_object_endpoint(
    lineage_id: int,
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    context: Annotated[ModulePatchObjectContext, Depends()],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    event_manager: Annotated[ApiEventManager, Depends(Provide[ApiContainer.event_manager])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    main_config: Annotated[MainConfig, Depends(Provide[ApiContainer.main_config])],
    object_in: BaseModel,
) -> BaseModel:
    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        session,
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

    target_codes_rule_config = main_config.get_as_model(
        "target_codes_module_or_valid_rule", TargetCodesModuleOrValidRuleConfig
    )
    if context.object_type in target_codes_rule_config.object_types and "Target_Codes" in changes:
        _guard_target_codes_in_module_or_valid(
            session,
            object_repository,
            module_object_repository,
            module.Module_ID,
            changes["Target_Codes"],
        )

    timepoint: datetime = datetime.now(timezone.utc)
    old_record, new_record = module_object_repository.patch_latest_module_object(
        session,
        module.Module_ID,
        context.object_type,
        lineage_id,
        changes,
        timepoint,
        user.UUID,
    )

    event: ModuleObjectPatchedEvent = event_manager.dispatch(
        session,
        ModuleObjectPatchedEvent.create(
            user,
            changes,
            timepoint,
            context.request_config_model,
            old_record,
            new_record,
        ),
    )
    new_record = event.payload.new_record

    # cache statics title if needed
    if "Title" in changes:
        valid_version = session.query(ObjectsTable).filter(ObjectsTable.Code == new_record.Code).first()
        if valid_version is None:
            object_static.Cached_Title = changes["Title"]
            session.add(object_static)

    session.add(new_record)
    session.flush()
    session.commit()

    response: BaseModel = context.response_config_model.pydantic_model.model_validate(new_record)
    return response
