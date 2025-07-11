import json
from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.objects.repositories.object_repository import ObjectRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class AtemporalDeleteObjectEndpointContext(BaseEndpointContext):
    object_type: str


@inject
def atemporal_delete_object_endpoint(
    lineage_id: int,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[AtemporalDeleteObjectEndpointContext, Depends()],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.atemporal_can_delete_object,
        user,
    )

    maybe_object: Optional[ObjectsTable] = object_repository.get_latest_by_id(
        session,
        context.object_type,
        lineage_id,
    )
    if not maybe_object:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object not found")

    timepoint: datetime = datetime.now(timezone.utc)
    if maybe_object.End_Validity is not None and maybe_object.End_Validity < timepoint:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Object is already deleted")

    log_before: str = json.dumps(maybe_object.to_dict())

    maybe_object.End_Validity = timepoint
    maybe_object.Modified_By_UUID = user.UUID
    maybe_object.Modified_Date = timepoint
    session.add(maybe_object)

    change_log: ChangeLogTable = ChangeLogTable(
        Object_Type=context.object_type,
        Object_ID=lineage_id,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Action_Type="atemporal_edit_object",
        Before=log_before,
        After=json.dumps(maybe_object.to_dict()),
    )
    session.add(change_log)

    session.flush()
    session.commit()

    return ResponseOK(message="OK")
