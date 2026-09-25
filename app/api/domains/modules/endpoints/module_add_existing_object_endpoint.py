import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_context_repository import ModuleObjectContextRepository
from app.api.domains.modules.services.object_provider import ObjectProvider
from app.api.domains.modules.types import ModuleObjectAction
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.api.types import ResponseOK
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.users import UsersTable


class ModuleAddExistingObject(BaseModel):
    object_uuid: uuid.UUID

    action: ModuleObjectAction
    explanation: str = Field("")
    conclusion: str = Field("")

    @field_validator("explanation", "conclusion", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(use_enum_values=True)


class ModuleAddExistingObjectEndpointContext(BaseEndpointContext):
    object_type: str
    allowed_object_types: list[str]


class ModuleAddExistingObjectService:
    def __init__(
        self,
        session: Session,
        object_provider: ObjectProvider,
        object_context_repository: ModuleObjectContextRepository,
        module: ModuleTable,
        user: UsersTable,
        object_in: ModuleAddExistingObject,
        context: ModuleAddExistingObjectEndpointContext,
    ):
        self._session: Session = session
        self._object_provider: ObjectProvider = object_provider
        self._object_context_repository: ModuleObjectContextRepository = object_context_repository
        self._module: ModuleTable = module
        self._user: UsersTable = user
        self._object_in: ModuleAddExistingObject = object_in
        self._context: ModuleAddExistingObjectEndpointContext = context
        self._timepoint: datetime = datetime.now(UTC)

    def process(self):
        object_data: dict | None = self._object_provider.get_by_id(self._session, self._object_in.object_uuid)
        if object_data is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown object for uuid")

        object_type: str = object_data["object_type"]
        object_id: int = object_data["object_id"]

        if object_type not in self._context.allowed_object_types:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Invalid object_type, accepted object_type are: {self._context.allowed_object_types}",
            )

        maybe_object_context: ModuleObjectContextTable | None = self._object_context_repository.get_by_ids(
            self._session,
            self._module.module_id,
            object_type,
            object_id,
        )

        try:
            if maybe_object_context is None:
                # If we never see this object code before then we can just create the context
                self._create_object_context(object_data)
            elif maybe_object_context.hidden:
                # If the context is hidden, then we knew this object, but is has been removed
                # We can just un-Hidden the context and set some additional properties
                self._update_object_context(maybe_object_context, object_data)
            else:
                # If the context is not hidden, then we are already tracking this object code
                # therefor we can not add it again
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Object already exists in module")

            self._create_object(object_data)

            self._session.flush()
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def _create_object_context(self, object_data: dict):
        object_context: ModuleObjectContextTable = ModuleObjectContextTable(
            module_id=self._module.module_id,
            object_type=object_data["object_type"],
            object_id=object_data["object_id"],
            code=object_data["code"],
            created_date=self._timepoint,
            modified_date=self._timepoint,
            created_by_id=self._user.UUID,
            modified_by_id=self._user.UUID,
            original_adjust_on=object_data["id"],
            action=self._object_in.action,
            explanation=self._object_in.explanation,
            conclusion=self._object_in.conclusion,
        )
        self._session.add(object_context)

    def _update_object_context(self, object_context: ModuleObjectContextTable, object_data: dict):
        object_context.hidden = False
        object_context.modified_date = self._timepoint
        object_context.modified_by_id = self._user.UUID
        object_context.original_adjust_on = object_data["id"]
        object_context.action = self._object_in.action
        object_context.explanation = self._object_in.explanation
        object_context.conclusion = self._object_in.conclusion
        self._session.add(object_context)

    def _create_object(self, object_data: dict):
        module_object = ModuleObjectsTable()

        for key, value in object_data.items():
            setattr(module_object, key, value)

        module_object.module_id = self._module.module_id
        module_object.adjust_on = object_data["id"]
        module_object.id = uuid.uuid4()
        module_object.modified_date = self._timepoint
        module_object.modified_by_id = self._user.UUID

        self._session.add(module_object)


@inject
def post_module_add_existing_object_endpoint(
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    object_provider: Annotated[ObjectProvider, Depends(Provide[ApiContainer.object_provider])],
    object_context_repository: Annotated[
        ModuleObjectContextRepository, Depends(Provide[ApiContainer.module_object_context_repository])
    ],
    context: Annotated[ModuleAddExistingObjectEndpointContext, Depends()],
    object_in: ModuleAddExistingObject,
) -> ResponseOK:
    permission_service.guard_valid_user(
        Permissions.module_can_add_existing_object_to_module,
        user,
        [module.module_manager_1_id, module.module_manager_2_id],
    )
    guard_module_not_locked(module)

    service = ModuleAddExistingObjectService(
        session,
        object_provider,
        object_context_repository,
        module,
        user,
        object_in,
        context,
    )
    service.process()

    return ResponseOK(message="OK")
