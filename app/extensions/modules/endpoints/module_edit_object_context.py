from datetime import datetime
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
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context,
)
from app.extensions.modules.models.models import ModuleObjectAction
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


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
        user: GebruikersTable,
        module: ModuleTable,
        object_context: ModuleObjectContextTable,
        user_role: Optional[str],
        object_in: ModuleEditObjectContext,
    ):
        self._db: Session = db
        self._user_role: Optional[str] = user_role
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._object_context: ModuleObjectContextTable = object_context
        self._object_in: ModuleEditObjectContext = object_in

    def handle(self) -> ResponseOK:
        self._guard_valid_user()

        changes: dict = self._object_in.dict(exclude_none=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            setattr(self._object_context, key, value)

        self._object_context.Modified_By_UUID = self._user.UUID
        self._object_context.Modified_Date = datetime.now()

        self._db.add(self._object_context)
        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )

    def _guard_valid_user(self):
        if self._module.is_manager(self._user.UUID):
            return
        if self._user_role is None:
            raise HTTPException(
                401, "Only module managers are allowed to patch the object"
            )
        if self._user_role != self._user.Rol:
            raise HTTPException(status_code=401, detail="Invalid user role")


class ModuleEditObjectContextEndpoint(Endpoint):
    def __init__(self, path: str, user_role: Optional[str]):
        self._path: str = path
        self._user_role: Optional[str] = user_role

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleEditObjectContext,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            object_context: ModuleObjectContextTable = Depends(
                depends_active_module_object_context
            ),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                module,
                object_context,
                self._user_role,
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

        user_role: Optional[str] = resolver_config.get("user_role", None)
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{object_type}" in path:
            raise RuntimeError("Missing {object_type} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ModuleEditObjectContextEndpoint(
            path=path,
            user_role=user_role,
        )
