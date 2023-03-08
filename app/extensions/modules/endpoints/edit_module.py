from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from app.core.dependencies import depends_db
from sqlalchemy.orm import Session

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleEdit(BaseModel):
    Temporary_Locked: Optional[bool] = Field(None, nullable=True)

    Title: Optional[str] = Field(None, nullable=True, min_length=3)
    Description: Optional[str] = Field(None, nullable=True, min_length=3)
    Module_Manager_1_UUID: Optional[uuid.UUID] = Field(None, nullable=True)
    Module_Manager_2_UUID: Optional[uuid.UUID] = Field(None, nullable=True)

    @validator("Module_Manager_2_UUID")
    def duplicate_manager(cls, v, values):
        if v is None:
            return v
        if not "Module_Manager_1_UUID" in values:
            return v
        if v == values["Module_Manager_1_UUID"]:
            raise ValueError("Duplicate manager")
        return v


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: GebruikersTable,
        module: ModuleTable,
        object_in: ModuleEdit,
    ):
        self._db: Session = db
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._object_in: ModuleEdit = object_in

    def handle(self) -> ResponseOK:
        self._guard_user_is_module_manager()

        changes: dict = self._object_in.dict(exclude_none=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            setattr(self._module, key, value)

        self._module.Modified_By_UUID = self._user.UUID
        self._module.Modified_Date = datetime.now()

        self._db.add(self._module)
        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )

    def _guard_user_is_module_manager(self):
        if not self._module.is_manager(self._user.UUID):
            raise HTTPException(401, "You are not allowed to modify this module")


class EditModuleEndpoint(Endpoint):
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        path: str,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleEdit,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                module,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit module",
            description=None,
            tags=["Modules"],
        )

        return router


class EditModuleEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_module"

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

        return EditModuleEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )