import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import String, func, insert, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
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
    object_type: str
    Title: str = Field(..., min_length=3)
    owner_1_id: uuid.UUID
    owner_2_id: uuid.UUID | None = Field(None)
    client_1_id: uuid.UUID | None = Field(None)

    Explanation: str = Field("")
    Conclusion: str = Field("")

    @field_validator("Explanation", "Conclusion", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    @field_validator("owner_2_id", mode="after")
    def duplicate_owner(cls, v, info):
        if v is None:
            return v
        if "owner_1_id" not in info.data:
            return v
        if v == info.data["owner_1_id"]:
            raise ValueError("Duplicate owner")
        return v


class NewObjectStaticResponse(BaseModel):
    object_type: str
    object_id: int
    code: str
    model_config = ConfigDict(from_attributes=True)


class ModuleAddNewObjectEndpointContext(BaseEndpointContext):
    object_type: str
    allowed_object_types: list[str]


class ModuleAddNewObjectService:
    def __init__(
        self,
        session: Session,
        module: ModuleTable,
        user: UsersTable,
        object_in: ModuleAddNewObject,
    ):
        self._session: Session = session
        self._module: ModuleTable = module
        self._user: UsersTable = user
        self._object_in: ModuleAddNewObject = object_in
        self._timepoint: datetime = datetime.now(UTC)

    def process(self) -> NewObjectStaticResponse:
        try:
            object_static: ObjectStaticsTable = self._create_new_object_static()
            self._create_object_context(object_static)
            self._create_object(object_static)

            self._session.flush()
            self._session.commit()

            return NewObjectStaticResponse.model_validate(object_static)
        except Exception:
            self._session.rollback()
            raise

    def _create_new_object_static(self) -> ObjectStaticsTable:
        generate_id_subq = (
            select(func.coalesce(func.max(ObjectStaticsTable.object_id), 0) + 1)
            .select_from(ObjectStaticsTable)
            .filter(ObjectStaticsTable.object_type == self._object_in.object_type)
            .scalar_subquery()
        )

        stmt = (
            insert(ObjectStaticsTable)
            .values(
                object_type=self._object_in.object_type,
                object_id=generate_id_subq,
                code=(self._object_in.object_type + "-" + func.cast(generate_id_subq, String)),
                # @todo: should be generated based on columns.statics
                owner_1_id=self._object_in.owner_1_id,
                owner_2_id=self._object_in.owner_2_id,
                client_1_id=self._object_in.client_1_id,
                cached_title=self._object_in.Title,
            )
            .returning(ObjectStaticsTable)
        )

        response: ObjectStaticsTable | None = self._session.execute(stmt).scalars().first()
        if response is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create new object static")

        return response

    def _create_object_context(self, object_static: ObjectStaticsTable):
        object_context: ModuleObjectContextTable = ModuleObjectContextTable(
            module_id=self._module.module_id,
            object_type=object_static.object_type,
            object_id=object_static.object_id,
            code=object_static.code,
            created_date=self._timepoint,
            modified_date=self._timepoint,
            created_by_id=self._user.UUID,
            modified_by_id=self._user.UUID,
            original_adjust_on=None,
            action=ModuleObjectActionFull.Create,
            explanation=self._object_in.Explanation,
            conclusion=self._object_in.Conclusion,
        )
        self._session.add(object_context)

    def _create_object(self, object_static: ObjectStaticsTable):
        module_object: ModuleObjectsTable = ModuleObjectsTable(
            id=uuid.uuid4(),
            module_id=self._module.module_id,
            object_type=object_static.object_type,
            object_id=object_static.object_id,
            code=object_static.code,
            title=self._object_in.Title,
            created_date=self._timepoint,
            modified_date=self._timepoint,
            created_by_id=self._user.UUID,
            modified_by_id=self._user.UUID,
        )
        self._session.add(module_object)


@inject
def post_module_add_new_object_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    context: Annotated[ModuleAddNewObjectEndpointContext, Depends()],
    object_in: ModuleAddNewObject,
) -> NewObjectStaticResponse:
    permission_service.guard_valid_user(
        Permissions.module_can_add_new_object_to_module,
        user,
        [module.module_manager_1_id, module.module_manager_2_id],
    )
    guard_module_not_locked(module)

    if object_in.object_type not in context.allowed_object_types:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid object_type, accepted object_type are: {context.allowed_object_types}",
        )

    service = ModuleAddNewObjectService(
        session,
        module,
        user,
        object_in,
    )
    response: NewObjectStaticResponse = service.process()

    return response
