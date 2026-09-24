import uuid
from copy import copy
from datetime import UTC, datetime
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.types import ModuleObjectAction, ModuleStatusCode, ModuleStatusCodeInternal
from app.api.domains.modules.utils import guard_module_is_locked
from app.api.domains.users.dependencies import depends_current_user
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleStatusHistoryTable, ModuleTable
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.tables.users import UsersTable
from app.core.utils.utils import table_to_dict


class CompleteModule(BaseModel):
    start_validity: datetime | None = Field(None)


class ObjectValidities(BaseModel):
    start: datetime
    end: datetime | None


def _guard_status_vastgesteld(module_status: str | None) -> None:
    if module_status is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Deze module heeft geen status")
    if module_status != ModuleStatusCode.Vastgesteld:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Alleen modules met status Vastgesteld kunnen worden afgesloten"
        )


def _get_validities(
    object_in: CompleteModule,
    module_object_context: ModuleObjectContextTable | None,
    timepoint: datetime,
) -> ObjectValidities:
    start_validity: datetime = object_in.start_validity or copy(timepoint)
    end_validity: datetime | None = None

    # If the object action is "Terminate" then we set the default end_validity to now
    if module_object_context and module_object_context.action == ModuleObjectAction.Terminate:
        end_validity = start_validity

    return ObjectValidities(
        start=start_validity,
        end=end_validity,
    )


def _create_objects(
    session: Session,
    module_object_repository: ModuleObjectRepository,
    user: UsersTable,
    module: ModuleTable,
    object_in: CompleteModule,
    timepoint: datetime,
) -> None:
    module_objects: list[ModuleObjectsTable] = module_object_repository.get_objects_in_time(
        session,
        module.module_id,
        timepoint,
    )

    for module_object_table in module_objects:
        module_object_dict: dict[str, Any] = table_to_dict(module_object_table)
        new_object: ObjectsTable = ObjectsTable()

        # Copy module object into the new object
        for key, value in module_object_dict.items():
            if key in ["module_id"]:
                continue
            setattr(new_object, key, copy(value))

        new_object.adjust_on = module_object_dict["id"]
        new_object.id = uuid.uuid4()

        new_object.modified_by_id = user.UUID
        new_object.modified_date = timepoint

        validities: ObjectValidities = _get_validities(
            object_in,
            module_object_table.module_object_context,
            timepoint,
        )
        new_object.start_validity = validities.start
        new_object.end_validity = validities.end

        statics: ObjectStaticsTable = (
            session.query(ObjectStaticsTable).filter(ObjectStaticsTable.code == new_object.code).one()
        )
        statics.cached_title = new_object.Title
        session.add(new_object)
        session.add(statics)


@inject
def post_complete_module_endpoint(
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    object_in: CompleteModule,
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_activate_module,
        user,
        [module.module_manager_1_id, module.module_manager_2_id],
    )
    guard_module_is_locked(module)
    _guard_status_vastgesteld(module.current_status)

    timepoint: datetime = datetime.now(UTC)

    try:
        status = ModuleStatusHistoryTable(
            module_id=module.module_id,
            status=ModuleStatusCodeInternal.Module_afgerond,
            created_date=timepoint,
            created_by_id=user.UUID,
        )
        session.add(status)

        _create_objects(session, module_object_repository, user, module, object_in, timepoint)

        module.closed = True
        module.successful = True
        module.modified_by_id = user.UUID
        module.modified_date = timepoint
        session.add(module)

        session.flush()
        session.commit()

    except Exception:
        session.rollback()
        raise

    return ResponseOK(message="OK")
