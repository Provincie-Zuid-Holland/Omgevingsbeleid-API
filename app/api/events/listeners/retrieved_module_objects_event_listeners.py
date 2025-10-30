from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.objects.services import ResolveChildObjectsViaHierarchyServiceFactory
from app.api.domains.objects.services.add_relations_service import AddRelationsService, AddRelationsServiceFactory
from app.api.domains.objects.services.resolve_child_objects_via_hierarchy_service import (
    ResolveChildObjectsViaHierarchyService,
    ResolveChildObjectsViaHierarchyConfig,
)
from app.api.domains.werkingsgebieden.services.join_werkingsgebieden import (
    JoinWerkingsgebiedenService,
    JoinWerkingsgebiedenServiceFactory,
)
from app.api.events.listeners.retrieved_objects_event_listeners import (
    GetColumnImagesListenerBase,
    JoinDocumentsListenerBase,
    EventRMO,
)
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.core.services.event.types import Listener
from app.core.types import DynamicObjectModel


class GetColumnImagesForModuleObjectListener(GetColumnImagesListenerBase[RetrievedModuleObjectsEvent]):
    pass


class JoinWerkingsgebiedToModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(
        self, session: Session, event: RetrievedModuleObjectsEvent
    ) -> Optional[RetrievedModuleObjectsEvent]:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event


class AddRelationsToModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: AddRelationsServiceFactory):
        self._service_factory: AddRelationsServiceFactory = service_factory

    def handle_event(
        self, session: Session, event: RetrievedModuleObjectsEvent
    ) -> Optional[RetrievedModuleObjectsEvent]:
        add_service: AddRelationsService = self._service_factory.create_service(
            session,
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event


class JoinDocumentsToModuleObjectsListener(JoinDocumentsListenerBase[RetrievedModuleObjectsEvent]):
    pass


class ResolveChildObjectsViaHierarchyToModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: ResolveChildObjectsViaHierarchyServiceFactory):
        self._service_factory: ResolveChildObjectsViaHierarchyServiceFactory = service_factory

    def handle_event(
        self, session: Session, event: RetrievedModuleObjectsEvent
    ) -> Optional[RetrievedModuleObjectsEvent]:
        config: Optional[ResolveChildObjectsViaHierarchyConfig] = self._collect_config(event)
        if not config:
            return event

        resolve_service: ResolveChildObjectsViaHierarchyService = self._service_factory.create_service(
            session,
            event.payload.rows,
            config,
        )

        result_rows: List[BaseModel] = resolve_service.resolve_child_objects()
        event.payload.rows = result_rows

        return event

    def _collect_config(self, event: EventRMO) -> Optional[ResolveChildObjectsViaHierarchyConfig]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None
        if "resolve_child_objects_via_hierarchy_listener" not in event.context.response_model.service_config:
            return None

        service_config: dict = event.context.response_model.service_config[
            "resolve_child_objects_via_hierarchy_listener"
        ]
        return ResolveChildObjectsViaHierarchyConfig(
            to_field=service_config["to_field"],
            response_model=event.context.response_model,
        )
