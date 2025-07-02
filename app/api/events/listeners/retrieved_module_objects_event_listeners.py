from typing import List, Optional

from pydantic import BaseModel

from app.api.domains.objects.services.add_relations import AddRelationsService, AddRelationsServiceFactory
from app.api.domains.werkingsgebieden.services.join_werkingsgebieden import (
    JoinWerkingsgebiedenService,
    JoinWerkingsgebiedenServiceFactory,
)
from app.api.events.listeners.retrieved_objects_event_listeners import GetColumnImagesListenerBase
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.core.services.event.types import Listener


class GetColumnImagesForModuleObjectListener(GetColumnImagesListenerBase[RetrievedModuleObjectsEvent]):
    pass


class JoinWerkingsgebiedToModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(self, event: RetrievedModuleObjectsEvent) -> Optional[RetrievedModuleObjectsEvent]:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event


class AddRelationsToModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: AddRelationsServiceFactory):
        self._service_factory: AddRelationsServiceFactory = service_factory

    def handle_event(self, event: RetrievedModuleObjectsEvent) -> Optional[RetrievedModuleObjectsEvent]:
        add_service: AddRelationsService = self._service_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event
