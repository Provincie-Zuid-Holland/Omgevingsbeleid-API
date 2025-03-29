import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.models.models import ModuleStatusCodeInternal
from app.extensions.modules.permissions import ModulesPermissions
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ModuleCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str = Field(..., min_length=3)
    Module_Manager_1_UUID: uuid.UUID
    Module_Manager_2_UUID: Optional[uuid.UUID] = Field(None)

    @field_validator("Module_Manager_2_UUID", mode="after")
    def duplicate_manager(cls, v, info):
        if v is None:
            return v
        if "Module_Manager_1_UUID" not in info.data:
            return v
        if v == info.data["Module_Manager_1_UUID"]:
            raise ValueError("Duplicate manager")
        return v


class ModuleCreatedResponse(BaseModel):
    Module_ID: int


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_in: ModuleCreate,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_in: ModuleCreate = object_in
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> ModuleCreatedResponse:
        module: ModuleTable = ModuleTable(
            Title=self._object_in.Title,
            Description=self._object_in.Description,
            Module_Manager_1_UUID=self._object_in.Module_Manager_1_UUID,
            Module_Manager_2_UUID=self._object_in.Module_Manager_2_UUID,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
            Activated=0,
            Closed=0,
            Successful=0,
            Temporary_Locked=0,
        )

        status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
            Status=ModuleStatusCodeInternal.Niet_Actief,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        module.status_history.append(status)

        self._db.add(module)
        self._db.add(status)

        self._db.flush()
        self._db.commit()

        return ModuleCreatedResponse(
            Module_ID=module.Module_ID,
        )


class CreateModuleEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(ModulesPermissions.can_create_module),
            ),
            db: Session = Depends(depends_db),
        ) -> ModuleCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ModuleCreatedResponse,
            summary=f"Create new module",
            description=None,
            tags=["Modules"],
        )

        return router


class CreateModuleEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_module"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return CreateModuleEndpoint(path=path)
