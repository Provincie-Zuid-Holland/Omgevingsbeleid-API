import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional, Type

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import String, func, insert, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.objects import ObjectsTable, ObjectStaticsTable
from app.core.tables.users import UsersTable


class AtemporalCreateObjectEndpointContext(BaseEndpointContext):
    object_type: str
    request_type: Type[BaseModel]
    response_type: Type[BaseModel]


def _create_new_static_object(
    db: Session,
    static_fields: Dict[str, Any],
    object_type: str,
    title: str,
) -> ObjectStaticsTable:
    generate_id_subq = (
        select(func.coalesce(func.max(ObjectStaticsTable.Object_ID), 0) + 1)
        .select_from(ObjectStaticsTable)
        .filter(ObjectStaticsTable.Object_Type == object_type)
        .scalar_subquery()
    )

    stmt = (
        insert(ObjectStaticsTable)
        .values(
            Object_Type=object_type,
            Object_ID=generate_id_subq,
            Code=(object_type + "-" + func.cast(generate_id_subq, String)),
            Cached_Title=title,
            # Unpack object_in static fields
            **(static_fields),
        )
        .returning(ObjectStaticsTable)
    )

    result: Optional[ObjectStaticsTable] = db.execute(stmt).scalars().first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create static object")
    return result


@inject
def atemporal_create_object_endpoint(
    object_in: BaseModel,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[AtemporalCreateObjectEndpointContext, Depends()],
) -> BaseModel:
    permission_service.guard_valid_user(Permissions.atemporal_can_create_object, user)

    object_in_data: Dict[str, Any] = object_in.model_dump(exclude_unset=True)

    static_fields: Dict[str, Any] = {}
    if "ObjectStatics" in object_in_data:
        static_fields = object_in_data["ObjectStatics"]
        del object_in_data["ObjectStatics"]

    try:
        object_static: ObjectStaticsTable = _create_new_static_object(
            db,
            static_fields,
            context.object_type,
            object_in_data.get("Title", ""),
        )

        timepoint: datetime = datetime.now(timezone.utc)
        new_object: ObjectsTable = ObjectsTable(
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            UUID=uuid.uuid4(),
            Created_Date=timepoint,
            Modified_Date=timepoint,
            Created_By_UUID=user.UUID,
            Modified_By_UUID=user.UUID,
            Start_Validity=timepoint,
            # Unpack object_in fields
            **(object_in_data),
        )
        db.add(new_object)
        db.flush()
        db.commit()

        response: BaseModel = context.response_type.model_validate(new_object)
        return response
    except Exception as e:
        db.rollback()
        raise e
