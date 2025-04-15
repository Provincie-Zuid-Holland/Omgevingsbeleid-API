import uuid
from copy import copy
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
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
    start_validity: Optional[datetime] = Field(None)


class ObjectValidities(BaseModel):
    start: datetime
    end: Optional[datetime]


def _guard_status_vastgesteld(module_status: Optional[str]) -> None:
    if module_status is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Deze module heeft geen status")
    if module_status != ModuleStatusCode.Vastgesteld:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Alleen modules met status Vastgesteld kunnen worden afgesloten"
        )


def _get_validities(
    object_in: CompleteModule,
    module_object_context: Optional[ModuleObjectContextTable],
    timepoint: datetime,
) -> ObjectValidities:
    start_validity: datetime = object_in.start_validity or copy(timepoint)
    end_validity: Optional[datetime] = None

    # If the object action is "Terminate" then we set the default end_validity to now
    if module_object_context and module_object_context.Action == ModuleObjectAction.Terminate:
        end_validity = start_validity

    return ObjectValidities(
        start=start_validity,
        end=end_validity,
    )


def _create_objects(
    db: Session,
    module_object_repository: ModuleObjectRepository,
    user: UsersTable,
    module: ModuleTable,
    object_in: CompleteModule,
    timepoint: datetime,
) -> None:
    module_objects: List[ModuleObjectsTable] = module_object_repository.get_objects_in_time(
        module.Module_ID,
        timepoint,
    )

    for module_object_table in module_objects:
        module_object_dict: Dict[str, Any] = table_to_dict(module_object_table)
        new_object: ObjectsTable = ObjectsTable()

        # Copy module object into the new object
        for key, value in module_object_dict.items():
            if key in ["Module_ID"]:
                continue
            setattr(new_object, key, copy(value))

        new_object.Adjust_On = module_object_dict["UUID"]
        new_object.UUID = uuid.uuid4()

        new_object.Modified_By_UUID = user.UUID
        new_object.Modified_Date = timepoint

        start_validity, end_validity = _get_validities(
            object_in,
            module_object_table.ModuleObjectContext,
            timepoint,
        )
        new_object.Start_Validity = start_validity
        new_object.End_Validity = end_validity

        statics: ObjectStaticsTable = (
            db.query(ObjectStaticsTable).filter(ObjectStaticsTable.Code == new_object.Code).one()
        )
        statics.Cached_Title = new_object.Title
        db.add(new_object)
        db.add(statics)


@inject
async def post_complete_module_endpoint(
    object_in: Annotated[CompleteModule, Depends()],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_activate_module,
        user,
        [module.Module_Manager_1_UUID, module.Module_Manager_2_UUID],
    )
    guard_module_is_locked(module)
    _guard_status_vastgesteld(module.Current_Status)

    timepoint: datetime = datetime.now(timezone.utc)

    try:
        status = ModuleStatusHistoryTable(
            Module_ID=module.Module_ID,
            Status=ModuleStatusCodeInternal.Module_afgerond,
            Created_Date=timepoint,
            Created_By_UUID=user.UUID,
        )
        db.add(status)

        _create_objects(db, module_object_repository, user, module, object_in, timepoint)

        module.Closed = True
        module.Successful = True
        module.Modified_By_UUID = user.UUID
        module.Modified_Date = timepoint
        db.add(module)

        db.flush()
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return ResponseOK(message="OK")
