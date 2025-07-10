import json
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional, Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.others import ChangeLogTable
from app.core.tables.users import UsersTable


class EditObjectStaticEndpointContext(BaseEndpointContext):
    object_type: str
    request_type: Type[BaseModel]
    result_type: Type[BaseModel]


@inject
def edit_object_static_endpoint(
    lineage_id: int,
    object_in: BaseModel,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[EditObjectStaticEndpointContext, Depends()],
) -> ResponseOK:
    changes: Dict[str, Any] = object_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to update")

    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        context.object_type,
        lineage_id,
    )
    if not object_static:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="lineage_id does not exist")

    permission_service.guard_valid_user(
        Permissions.can_patch_object_static,
        user,
        [
            object_static.Owner_1_UUID,
            object_static.Owner_2_UUID,
            object_static.Portfolio_Holder_1_UUID,
            object_static.Portfolio_Holder_2_UUID,
            object_static.Client_1_UUID,
        ],
    )

    log_before: str = json.dumps(object_static.to_dict())

    for key, value in changes.items():
        setattr(object_static, key, value)

    # This executes the validators on the result type
    # Making sure the final object meets all validation requirements
    _ = context.result_type.model_validate(object_static)

    change_log: ChangeLogTable = ChangeLogTable(
        Object_Type=context.object_type,
        Object_ID=lineage_id,
        Created_Date=datetime.now(timezone.utc),
        Created_By_UUID=user.UUID,
        Action_Type="edit_object_static",
        Action_Data=object_in.model_dump(),
        Before=log_before,
        After=json.dumps(object_static.to_dict()),
    )
    db.add(change_log)

    db.flush()
    db.commit()

    return ResponseOK(message="OK")
