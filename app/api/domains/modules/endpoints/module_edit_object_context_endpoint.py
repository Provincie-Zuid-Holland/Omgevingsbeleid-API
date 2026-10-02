import json
from datetime import UTC, datetime
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context,
    depends_module_object_latest_by_id,
)
from app.api.domains.modules.types import ModuleObjectAction
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class ModuleEditObjectContext(BaseModel):
    action: ModuleObjectAction | None = None
    explanation: str | None = None
    conclusion: str | None = None

    model_config = ConfigDict(use_enum_values=True)


@inject
def post_module_edit_object_context_endpoint(
    _: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module_object: Annotated[ModuleObjectsTable, Depends(depends_module_object_latest_by_id)],
    object_context: Annotated[ModuleObjectContextTable, Depends(depends_active_module_object_context)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    object_in: ModuleEditObjectContext,
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_edit_module_object_context,
        user,
        whitelisted_ids=[
            module_object.object_statics.owner_1_id,
            module_object.object_statics.owner_2_id,
            module_object.object_statics.portfolio_holder_1_id,
            module_object.object_statics.portfolio_holder_2_id,
            module_object.object_statics.client_1_id,
        ],
    )

    changes: dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to update")

    log_before: str = json.dumps(object_context.to_dict())

    for key, value in changes.items():
        setattr(object_context, key, value)

    timepoint: datetime = datetime.now(UTC)

    object_context.modified_by_id = user.UUID
    object_context.modified_date = timepoint

    session.add(object_context)

    change_log: ChangeLogTable = ChangeLogTable(
        object_type=object_context.object_type,
        object_id=object_context.object_id,
        created_date=timepoint,
        created_by_id=user.UUID,
        action_type="module_edit_object_context",
        action_data=object_in.model_dump_json(),
        before=log_before,
        after=json.dumps(object_context.to_dict()),
    )
    session.add(change_log)

    session.flush()
    session.commit()

    return ResponseOK(message="OK")
