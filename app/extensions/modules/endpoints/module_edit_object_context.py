from datetime import datetime
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context,
)
from app.extensions.modules.models.models import ModuleObjectAction
from app.extensions.modules.permissions import ModulesPermissions, guard_valid_user
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_permission_service,
)
from app.extensions.users.permission_service import PermissionService


class ModuleEditObjectContext(BaseModel):
    Action: Optional[ModuleObjectAction] = Field(None, nullable=True)
    Explanation: Optional[str] = Field(None, nullable=True)
    Conclusion: Optional[str] = Field(None, nullable=True)

    class Config:
        use_enum_values = True


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        permission_service: PermissionService,
        user: UsersTable,
        module: ModuleTable,
        object_context: ModuleObjectContextTable,
        object_in: ModuleEditObjectContext,
    ):
        self._db: Session = db
        self._permission_service: PermissionService = permission_service
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._object_context: ModuleObjectContextTable = object_context
        self._object_in: ModuleEditObjectContext = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> ResponseOK:
        guard_valid_user(
            self._permission_service,
            ModulesPermissions.can_edit_module_object_context,
            self._user,
            self._module,
        )

        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        log_before: str = json.dumps(self._object_context.to_dict())

        for key, value in changes.items():
            setattr(self._object_context, key, value)

        self._object_context.Modified_By_UUID = self._user.UUID
        self._object_context.Modified_Date = self._timepoint

        self._db.add(self._object_context)

        change_log: ChangeLogTable = ChangeLogTable(
            Object_Type=self._object_context.Object_Type,
            Object_ID=self._object_context.Object_ID,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Action_Type="module_edit_object_context",
            Action_Data=self._object_in.json(),
            Before=log_before,
            After=json.dumps(self._object_context.to_dict()),
        )
        self._db.add(change_log)

        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )


class ModuleEditObjectContextEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleEditObjectContext,
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            object_context: ModuleObjectContextTable = Depends(
                depends_active_module_object_context
            ),
            db: Session = Depends(depends_db),
            permission_service: PermissionService = Depends(depends_permission_service),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                permission_service,
                user,
                module,
                object_context,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit context of object in the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleEditObjectContextEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_edit_object_context"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{object_type}" in path:
            raise RuntimeError("Missing {object_type} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ModuleEditObjectContextEndpoint(path=path)
