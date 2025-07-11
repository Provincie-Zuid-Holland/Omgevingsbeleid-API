import json
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional, Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
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


class AtemporalEditObjectEndpointContext(BaseEndpointContext):
    object_type: str
    request_type: Type[BaseModel]


@inject
def atemporal_edit_object_endpoint(
    lineage_id: int,
    object_in: BaseModel,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    object_repository: Annotated[ObjectRepository, Depends(Provide[ApiContainer.object_repository])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[AtemporalEditObjectEndpointContext, Depends()],
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.atemporal_can_edit_object,
        user,
    )

    maybe_object: Optional[ObjectsTable] = object_repository.get_latest_by_id(
        session,
        context.object_type,
        lineage_id,
    )
    if not maybe_object:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to update")

    log_before: str = json.dumps(maybe_object.to_dict())

    for key, value in changes.items():
        setattr(maybe_object, key, value)

    timepoint: datetime = datetime.now(timezone.utc)
    maybe_object.Modified_By_UUID = user.UUID
    maybe_object.Modified_Date = timepoint
    session.add(maybe_object)

    if "Title" in changes:
        maybe_object.ObjectStatics.Cached_Title = changes["Title"]
        session.add(maybe_object.ObjectStatics)

    change_log: ChangeLogTable = ChangeLogTable(
        Object_Type=context.object_type,
        Object_ID=lineage_id,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Action_Type="atemporal_edit_object",
        Action_Data=changes,
        Before=log_before,
        After=json.dumps(maybe_object.to_dict()),
    )
    session.add(change_log)

    session.flush()
    session.commit()

    return ResponseOK(message="OK")
