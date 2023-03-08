from copy import copy
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.dynamic.db.objects_table import ObjectsTable
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_module_object_repository,
    depends_module_status_repository,
)
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)
from app.extensions.modules.repository.module_status_repository import (
    ModuleStatusRepository,
)
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import depends_current_active_user


class ObjectSpecifiekeGeldigheid(BaseModel):
    Object_Type: str
    Object_ID: int
    Start_Validity: Optional[datetime] = Field(None, nullable=True)
    End_Validity: Optional[datetime] = Field(None, nullable=True)


class CompleteModule(BaseModel):
    ObjectSpecifiekeGeldigheden: List[ObjectSpecifiekeGeldigheid] = []


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        module_status_repository: ModuleStatusRepository,
        module_object_repository: ModuleObjectRepository,
        event_dispatcher: EventDispatcher,
        user: GebruikersTable,
        module: ModuleTable,
        object_in: CompleteModule,
    ):
        self._db: Session = db
        self._module_status_repository: ModuleStatusRepository = (
            module_status_repository
        )
        self._module_object_repository: ModuleObjectRepository = (
            module_object_repository
        )
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._object_in: CompleteModule = object_in
        self._timepoint: datetime = datetime.now()

    def handle(self) -> ResponseOK:
        self._guard_status_must_be_vigerend()

        try:
            new_status: ModuleStatusHistoryTable = self._patch_status()
            self._create_objects()
            self._close_module()

            self._db.flush()
            self._db.commit()

            self._dispatch_status_changed_event(new_status)

        except Exception as e:
            self._db.rollback()
            raise HTTPException(500, "Could not complete the module")

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
        module_objects: List[dict] = self._module_object_repository.get_objects_in_time(
            self._module.Module_ID,
            self._timepoint,
        )

        for module_object in module_objects:
            new_object: ObjectsTable = ObjectsTable()
            # Copy module object into the new object
            for key, value in module_object.items():
                if key in ["Module_ID"]:
                    continue
                setattr(new_object, key, copy(value))

            new_object.Adjust_On = module_object.get("UUID")
            new_object.UUID = uuid4()

            new_object.Modified_By_UUID = self._user.UUID
            new_object.Modified_Date = self._timepoint

            start_validity, end_validity = self._get_validities(
                module_object.get("Object_Type"),
                module_object.get("Object_ID"),
            )
            new_object.Start_Validity = start_validity
            new_object.End_Validity = end_validity

            self._db.add(new_object)

    def _get_validities(
        self,
        object_type: str,
        object_id: int,
    ) -> Tuple[datetime, Optional[datetime]]:
        start_validity: datetime = copy(self._timepoint)
        end_validity: Optional[datetime] = None

        # Inherit from module
        if self._module.Start_Validity is not None:
            start_validity = self._module.Start_Validity
        if self._module.End_Validity is not None:
            end_validity = self._module.End_Validity

        # Overwrite if specified
        for specifics in self._object_in.ObjectSpecifiekeGeldigheden:
            if specifics.Object_ID != object_id or specifics.Object_Type != object_type:
                continue
            if specifics.Start_Validity is not None:
                start_validity = specifics.Start_Validity
            if specifics.End_Validity is not None:
                end_validity = specifics.End_Validity

        return (start_validity, end_validity)

    def _patch_status(self) -> ModuleStatusHistoryTable:
        status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
            Module_ID=self._module.Module_ID,
            Status="Vigerend gearchiveerd",
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

    def _guard_status_must_be_vigerend(self):
        status: Optional[
            ModuleStatusHistoryTable
        ] = self._module_status_repository.get_latest_for_module(self._module.Module_ID)
        if status is None:
            raise HTTPException(400, "Deze module heeft geen status")
        if status.Status != ModuleStatusCode.Vigerend:
            raise HTTPException(
                400, "Alleen modules met status Vigerend kunnen worden afgesloten"
            )


class CompleteModuleEndpoint(Endpoint):
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        path: str,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: CompleteModule,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
            module_status_repository: ModuleStatusRepository = Depends(
                depends_module_status_repository
            ),
            module_object_repository: ModuleObjectRepository = Depends(
                depends_module_object_repository
            ),
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

        return CompleteModuleEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )