from typing import List
from pydantic import BaseModel


from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.converter import Converter
from app.extensions.relations.service.add_relations import AddRelationsService


class RetrievedObjectsListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, converter: Converter):
        self._converter: Converter = converter

    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        add_service: AddRelationsService = AddRelationsService(
            self._converter,
            event.get_db(),
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event
