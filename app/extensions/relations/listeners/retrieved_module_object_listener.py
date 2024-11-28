from typing import List, Optional

from pydantic import BaseModel

from app.dynamic.converter import Converter
from app.dynamic.event.types import Listener
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.relations.service.add_relations import AddRelationsService


class RetrievedModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, converter: Converter):
        self._converter: Converter = converter

    def handle_event(self, event: RetrievedModuleObjectsEvent) -> Optional[RetrievedModuleObjectsEvent]:
        add_service: AddRelationsService = AddRelationsService(
            self._converter,
            event.get_db(),
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event
