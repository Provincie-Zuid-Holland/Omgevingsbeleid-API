from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.modules.repository.object_provider import ObjectProvider


class WerkingsgebiedRelatedObjectService:
    def __init__(
        self,
        event: RetrievedObjectsEvent,
        target_field: str,
    ):
        self._target_field: str = target_field
        self._event_objects: List[BaseModel] = event.payload.rows
        self._db: Session = event.get_db()
        self._object_provider = ObjectProvider(
            object_repository=ObjectRepository(self._db),
            module_object_repository=ModuleObjectRepository(self._db),
        )

    def process(self):
        for item in self._event_objects:
            related_objects = self._object_provider.list_all_objects_related_to_werkingsgebied(
                werkingsgebied_code=item.Code
            )
            setattr(item, self._target_field, related_objects)
        return self._event_objects


class WerkingsgebiedRelatedObjectsListener(Listener[RetrievedObjectsEvent]):
    TARGET_FIELD: str = "Related_Objects"
    TARGET_SERVICE: str = "insert_computed_fields"

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        if not self.TARGET_SERVICE in event.context.response_model.service_config:
            return event

        fields = event.context.response_model.service_config[self.TARGET_SERVICE]["fields"]
        if not any(field.get("field_name") == self.TARGET_FIELD for field in fields):
            return event

        service = WerkingsgebiedRelatedObjectService(event, self.TARGET_FIELD)
        result_rows = service.process()

        event.payload.rows = result_rows
        return event
