from typing import List, Optional

from pydantic import BaseModel

from app.api.domains.objects.services.add_relations import AddRelationsService, AddRelationsServiceFactory
from app.api.domains.werkingsgebieden.services.join_werkingsgebieden import (
    JoinWerkingsgebiedenService,
    JoinWerkingsgebiedenServiceFactory,
)
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.types import Listener


class AddRelationsToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, relations_factory: AddRelationsServiceFactory):
        self._relations_factory: AddRelationsServiceFactory = relations_factory

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        add_service: AddRelationsService = self._relations_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event


class JoinWerkingsgebeidenToObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: JoinWerkingsgebiedenServiceFactory):
        self._service_factory: JoinWerkingsgebiedenServiceFactory = service_factory

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        join_service: JoinWerkingsgebiedenService = self._service_factory.create_service(
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = join_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event
