from datetime import datetime
from typing import Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pydantic
from app.core.dependencies import depends_db

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_and_activated_module,
    depends_active_module_object_context_curried,
    depends_module_object_repository,
)
from app.extensions.modules.event.module_object_patched_event import (
    ModuleObjectPatchedEvent,
)
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        converter: Converter,
        object_config_id: str,
        object_type: str,
        request_model: Model,
        response_type: Type[pydantic.BaseModel],
        event_dispatcher: EventDispatcher,
        db: Session,
        module_object_repository: ModuleObjectRepository,
        user_role: Optional[str],
        user: GebruikersTable,
        module: ModuleTable,
        changes: dict,
        lineage_id: int,
    ):
        self._converter: Converter = converter
        self._object_config_id: str = object_config_id
        self._object_type: str = object_type
        self._request_model: Model = request_model
        self._response_type: Type[pydantic.BaseModel] = response_type

        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._db: Session = db
        self._module_object_repository: ModuleObjectRepository = (
            module_object_repository
        )

        self._user_role: Optional[str] = user_role
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._changes: dict = changes
        self._lineage_id: int = lineage_id
        self._timepoint: datetime = datetime.now()

    def handle(self):
        self._guard_valid_user()
        self._guard_module_not_locked()

        if not self._changes:
            raise HTTPException(400, "Nothing to update")

        new_record: ModuleObjectsTable = (
            self._module_object_repository.patch_latest_module_object(
                self._module.Module_ID,
                self._object_type,
                self._lineage_id,
                self._changes,
                self._timepoint,
                self._user.UUID,
            )
        )

        event: ModuleObjectPatchedEvent = self._event_dispatcher.dispatch(
            ModuleObjectPatchedEvent.create(
                self._user,
                self._changes,
                self._timepoint,
                self._request_model,
                new_record,
            )
        )
        new_record = event.payload.new_record

        self._db.add(new_record)
        self._db.flush()
        self._db.commit()

        response = self._response_type.from_orm(new_record)
        return response

    def _guard_valid_user(self):
        if self._module.is_manager(self._user.UUID):
            return
        if self._user_role is None:
            raise HTTPException(
                401, "Only module managers are allowed to patch the object"
            )
        if self._user_role != self._user.Rol:
            raise HTTPException(status_code=401, detail="Invalid user role")

    def _guard_module_not_locked(self):
        if self._module.Temporary_Locked:
            raise HTTPException(status_code=400, detail="The module is locked")


class ModulePatchObjectEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        path: str,
        object_config_id: str,
        object_type: str,
        request_model: Model,
        response_type: Type[pydantic.BaseModel],
        user_role: Optional[str],
    ):
        self._converter: Converter = converter
        self._path: str = path
        self._object_config_id: str = object_config_id
        self._object_type: str = object_type
        self._request_model: Model = request_model
        self._request_type: Type[pydantic.BaseModel] = request_model.pydantic_model
        self._response_type: Type[pydantic.BaseModel] = response_type
        self._user_role: Optional[str] = user_role

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            object_in: self._request_type,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_and_activated_module),
            module_object_context=Depends(
                depends_active_module_object_context_curried(self._object_type)
            ),
            db: Session = Depends(depends_db),
            module_object_repository: ModuleObjectRepository = Depends(
                depends_module_object_repository
            ),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> self._response_type:
            handler: EndpointHandler = EndpointHandler(
                self._converter,
                self._object_config_id,
                self._object_type,
                self._request_model,
                self._response_type,
                event_dispatcher,
                db,
                module_object_repository,
                self._user_role,
                user,
                module,
                object_in.dict(exclude_none=True),
                lineage_id,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PATCH"],
            response_model=self._response_type,
            summary=f"Add a new version to the {self._object_type} lineage in a module",
            description=None,
            tags=[self._object_type],
        )

        return router


class ModulePatchObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_patch_object"

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
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        user_role: Optional[str] = resolver_config.get("user_role", None)
        request_model = models_resolver.get(resolver_config.get("request_model"))
        response_model = models_resolver.get(resolver_config.get("response_model"))
        response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

        return ModulePatchObjectEndpoint(
            converter=converter,
            path=path,
            object_config_id=api.id,
            object_type=api.object_type,
            request_model=request_model,
            response_type=response_type,
            user_role=user_role,
        )