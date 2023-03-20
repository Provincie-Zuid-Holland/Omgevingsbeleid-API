from typing import Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.dependencies import depends_db
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_module_object_context_repository,
    depends_object_provider,
)
from app.extensions.modules.models.models import ModuleObjectAction
from app.extensions.modules.permissions import ModulesPermissions
from app.extensions.modules.repository import ModuleObjectContextRepository
from app.extensions.modules.repository.object_provider import ObjectProvider
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_permission_service,
)
from app.dynamic.utils.response import ResponseOK
from app.extensions.users.permission_service import PermissionService


class ModuleAddExistingObject(BaseModel):
    Object_UUID: uuid.UUID

    Action: ModuleObjectAction
    Explanation: str
    Conclusion: str

    class Config:
        use_enum_values = True


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_provider: ObjectProvider,
        object_context_repository: ModuleObjectContextRepository,
        permission_service: PermissionService,
        user: GebruikersTable,
        module: ModuleTable,
        object_in: ModuleAddExistingObject,
    ):
        self._db: Session = db
        self._object_provider = object_provider
        self._object_context_repository: ModuleObjectContextRepository = (
            object_context_repository
        )
        self._permission_service: PermissionService = permission_service
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._object_in: ModuleAddExistingObject = object_in
        self._timepoint: datetime = datetime.now()

    def handle(self):
        self._guard_valid_user()
        self._guard_module_not_locked()

        object_data: Optional[dict] = self._object_provider.get_by_uuid(
            self._object_in.Object_UUID
        )
        if object_data is None:
            raise HTTPException(400, "Unknown object for uuid")

        object_type: str = object_data.get("Object_Type")
        object_id: int = object_data.get("Object_ID")
        maybe_object_context: Optional[
            ModuleObjectContextTable
        ] = self._object_context_repository.get_by_ids(
            self._module.Module_ID,
            object_type,
            object_id,
        )

        try:
            if maybe_object_context is None:
                # If we never seen this object code before then we can just create the context
                self._create_object_context(object_data)
            elif maybe_object_context.Hidden:
                # If the context is hidden, then we knew this object, but is has been removed
                # We can just un-Hidden the context and set some additional properties
                self._update_object_context(maybe_object_context, object_data)
            else:
                # If the context is not hidden, then we are already tracking this object code
                # therefor we can not add it again
                raise HTTPException(400, "Object already exists in module")

            self._create_object(object_data)

            self._db.flush()
            self._db.commit()
        except HTTPException as e:
            self._db.rollback()
            raise e
        except Exception as e:
            self._db.rollback()
            raise HTTPException(500, "Could not add object to the module")

        return ResponseOK(
            message="OK",
        )

    def _create_object_context(self, object_data: dict):
        object_context: ModuleObjectContextTable = ModuleObjectContextTable(
            Module_ID=self._module.Module_ID,
            Object_Type=object_data.get("Object_Type"),
            Object_ID=object_data.get("Object_ID"),
            Code=object_data.get("Code"),
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
            Original_Adjust_On=object_data.get("UUID"),
            Action=self._object_in.Action,
            Explanation=self._object_in.Explanation,
            Conclusion=self._object_in.Conclusion,
        )
        self._db.add(object_context)

    def _update_object_context(
        self, object_context: ModuleObjectContextTable, object_data: dict
    ):
        object_context.Hidden = False
        object_context.Modified_Date = self._timepoint
        object_context.Modified_By_UUID = self._user.UUID
        object_context.Original_Adjust_On = object_data.get("UUID")
        object_context.Explanation = self._object_in.Explanation
        object_context.Conclusion = self._object_in.Conclusion
        self._db.add(object_context)

    def _create_object(self, object_data: dict):
        module_object: ModuleObjectsTable = ModuleObjectsTable()

        for key, value in object_data.items():
            setattr(module_object, key, value)

        module_object.Module_ID = self._module.Module_ID
        module_object.Adjust_On = object_data.get("UUID")
        module_object.UUID = uuid.uuid4()
        module_object.Modified_Date = self._timepoint
        module_object.Modified_By_UUID = self._user.UUID

        self._db.add(module_object)

    def _guard_valid_user(self):
        if self._module.is_manager(self._user.UUID):
            return

        if not self._permission_service.has_permission(
            ModulesPermissions.can_add_existing_object_to_module, self._user
        ):
            raise HTTPException(status_code=401, detail="Invalid user role")

    def _guard_module_not_locked(self):
        if self._module.Temporary_Locked:
            raise HTTPException(status_code=400, detail="The module is locked")


class ModuleAddExistingObjectEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleAddExistingObject,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
            object_provider: ObjectProvider = Depends(depends_object_provider),
            object_context_repository: ModuleObjectContextRepository = Depends(
                depends_module_object_context_repository
            ),
            permission_service: PermissionService = Depends(depends_permission_service),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_provider,
                object_context_repository,
                permission_service,
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
            summary=f"Add existing object to the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleAddExistingObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_add_existing_object"

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

        return ModuleAddExistingObjectEndpoint(path=path)
