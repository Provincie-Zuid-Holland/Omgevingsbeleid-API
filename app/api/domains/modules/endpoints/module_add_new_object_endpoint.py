import uuid
from datetime import datetime, timezone
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import String, func, insert, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.types import ModuleObjectActionFull
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable


class ModuleAddNewObject(BaseModel):
    Object_Type: str
    Title: str = Field(..., min_length=3)
    Owner_1_UUID: uuid.UUID
    Owner_2_UUID: Optional[uuid.UUID] = Field(None)
    Client_1_UUID: Optional[uuid.UUID] = Field(None)

    Explanation: str = Field("")
    Conclusion: str = Field("")

    @field_validator("Explanation", "Conclusion", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @field_validator("Owner_2_UUID", mode="after")
    def duplicate_owner(cls, v, info):
        if v is None:
            return v
        if "Owner_1_UUID" not in info.data:
            return v
        if v == info.data["Owner_1_UUID"]:
            raise ValueError("Duplicate owner")
        return v


class NewObjectStaticResponse(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    model_config = ConfigDict(from_attributes=True)


class ModuleAddNewObjectEndpointContext(BaseEndpointContext):
    object_type: str
    allowed_object_types: List[str]


class ModuleAddNewObjectService:
    def __init__(
        self,
        db: Session,
        module: ModuleTable,
        user: UsersTable,
        object_in: ModuleAddNewObject,
    ):
        self._db: Session = db
        self._module: ModuleTable = module
        self._user: UsersTable = user
        self._object_in: ModuleAddNewObject = object_in
        self._timepoint: datetime = datetime.now(timezone.utc)

    def process(self) -> NewObjectStaticResponse:
        try:
            object_static: ObjectStaticsTable = self._create_new_object_static()
            self._create_object_context(object_static)
            self._create_object(object_static)

            self._db.flush()
            self._db.commit()

            return NewObjectStaticResponse.model_validate(object_static)
        except Exception:
            self._db.rollback
            raise

    def _create_new_object_static(self) -> ObjectStaticsTable:
        generate_id_subq = (
            select(func.coalesce(func.max(ObjectStaticsTable.Object_ID), 0) + 1)
            .select_from(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == self._object_in.Object_Type)
            .scalar_subquery()
        )

        stmt = (
            insert(ObjectStaticsTable)
            .values(
                Object_Type=self._object_in.Object_Type,
                Object_ID=generate_id_subq,
                Code=(self._object_in.Object_Type + "-" + func.cast(generate_id_subq, String)),
                # @todo: should be generated based on columns.statics
                Owner_1_UUID=self._object_in.Owner_1_UUID,
                Owner_2_UUID=self._object_in.Owner_2_UUID,
                Client_1_UUID=self._object_in.Client_1_UUID,
                Cached_Title=self._object_in.Title,
            )
            .returning(ObjectStaticsTable)
        )

        response: Optional[ObjectStaticsTable] = self._db.execute(stmt).scalars().first()
        if response is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create new object static")

        return response

    def _create_object_context(self, object_static: ObjectStaticsTable):
        object_context: ModuleObjectContextTable = ModuleObjectContextTable(
            Module_ID=self._module.Module_ID,
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
            Original_Adjust_On=None,
            Action=ModuleObjectActionFull.Create,
            Explanation=self._object_in.Explanation,
            Conclusion=self._object_in.Conclusion,
        )
        self._db.add(object_context)

    def _create_object(self, object_static: ObjectStaticsTable):
        module_object: ModuleObjectsTable = ModuleObjectsTable(
            Module_ID=self._module.Module_ID,
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            UUID=uuid.uuid4(),
            Title=self._object_in.Title,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(module_object)


@inject
async def post_module_add_new_object(
    object_in: Annotated[ModuleAddNewObject, Depends()],
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[ModuleAddNewObjectEndpointContext, Depends()],
) -> NewObjectStaticResponse:
    permission_service.guard_valid_user(
        Permissions.module_can_add_new_object_to_module,
        user,
        [module.Module_Manager_1_UUID, module.Module_Manager_2_UUID],
    )
    guard_module_not_locked(module)

    if object_in.Object_Type not in context.allowed_object_types:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid Object_Type, accepted object_type are: {context.allowed_object_types}",
        )

    service = ModuleAddNewObjectService(
        db,
        module,
        user,
        object_in,
    )
    response: NewObjectStaticResponse = service.process()

    return response
