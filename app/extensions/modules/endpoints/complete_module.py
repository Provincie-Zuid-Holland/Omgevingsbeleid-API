import uuid
from copy import copy
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.core.utils.utils import table_to_dict
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_module_object_repository,
    depends_module_status_repository,
)
from app.extensions.modules.event.module_status_changed_event import ModuleStatusChangedEvent
from app.extensions.modules.models.models import ModuleObjectAction, ModuleStatusCodeInternal
from app.extensions.modules.permissions import guard_module_is_locked, guard_status_must_be_vastgesteld
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.modules.repository.module_status_repository import ModuleStatusRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleObjectContextShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str

    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Action: str
    model_config = ConfigDict(from_attributes=True)


class ModuleObjectContext(ModuleObjectContextShort):
    Explanation: str
    Conclusion: str


class ObjectSpecifiekeGeldigheid(BaseModel):
    Object_Type: str
    Object_ID: int
    Start_Validity: Optional[datetime] = Field(None, nullable=True)


class CompleteModule(BaseModel):
    Default_Start_Validity: Optional[datetime] = Field(None, nullable=True)
    ObjectSpecifiekeGeldigheden: List[ObjectSpecifiekeGeldigheid] = []


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        module_status_repository: ModuleStatusRepository,
        module_object_repository: ModuleObjectRepository,
        event_dispatcher: EventDispatcher,
        user: UsersTable,
        module: ModuleTable,
        object_in: CompleteModule,
    ):
        self._db: Session = db
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._object_in: CompleteModule = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> ResponseOK:
        guard_module_is_locked(self._module)
        guard_status_must_be_vastgesteld(self._module)

        try:
            new_status: ModuleStatusHistoryTable = self._patch_status()
            self._create_objects()
            self._close_module()

            self._db.flush()
            self._db.commit()

            self._dispatch_status_changed_event(new_status)

        except Exception as e:
            self._db.rollback()
            raise

        return ResponseOK(
            message="OK",
        )

    def _dispatch_status_changed_event(self, new_status: ModuleStatusHistoryTable):
        self._event_dispatcher.dispatch(
            ModuleStatusChangedEvent.create(
                self._module,
                new_status,
            )
        )

    def _create_objects(self):
        module_objects: List[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._timepoint,
        )

        for module_object_table in module_objects:
            module_object_dict = table_to_dict(module_object_table)
            new_object: ObjectsTable = ObjectsTable()

            # Copy module object into the new object
            for key, value in module_object_dict.items():
                if key in ["Module_ID"]:
                    continue
                setattr(new_object, key, copy(value))

            new_object.Adjust_On = module_object_dict.get("UUID")
            new_object.UUID = uuid.uuid4()

            new_object.Modified_By_UUID = self._user.UUID
            new_object.Modified_Date = self._timepoint

            start_validity, end_validity = self._get_validities(
                module_object_dict.get("Object_Type"),
                module_object_dict.get("Object_ID"),
                module_object_table.ModuleObjectContext,
            )
            new_object.Start_Validity = start_validity
            new_object.End_Validity = end_validity

            statics = self._db.query(ObjectStaticsTable).filter(ObjectStaticsTable.Code == new_object.Code).one()
            statics.Cached_Title = new_object.Title
            self._db.add(new_object)
            self._db.add(statics)

    def _get_validities(
        self,
        object_type: str,
        object_id: int,
        module_object_context: Optional[ModuleObjectContext],
    ) -> Tuple[datetime, Optional[datetime]]:
        start_validity: datetime = self._object_in.Default_Start_Validity or copy(self._timepoint)
        end_validity: Optional[datetime] = None

        for specifics in self._object_in.ObjectSpecifiekeGeldigheden:
            if (specifics.Object_ID, specifics.Object_Type) == (object_id, object_type):
                start_validity = specifics.Start_Validity or start_validity

        # If the object action is "Terminate" then we set the default end_validity to now
        if module_object_context and module_object_context.Action == ModuleObjectAction.Terminate:
            end_validity = start_validity

        return start_validity, end_validity

    def _patch_status(self) -> ModuleStatusHistoryTable:
        status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
            Module_ID=self._module.Module_ID,
            Status=ModuleStatusCodeInternal.Module_afgerond,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(status)
        return status

    def _close_module(self):
        self._module.Closed = 1
        self._module.Successful = 1
        self._module.Modified_By_UUID = self._user.UUID
        self._module.Modified_Date = self._timepoint
        self._db.add(self._module)


class CompleteModuleEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: CompleteModule,
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
            module_status_repository: ModuleStatusRepository = Depends(depends_module_status_repository),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                module_status_repository,
                module_object_repository,
                event_dispatcher,
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
            summary=f"Complete a module (Successful)",
            description=None,
            tags=["Modules"],
        )

        return router


class CompleteModuleEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "complete_module"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")

        return CompleteModuleEndpoint(path=path)
