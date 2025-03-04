from typing import List, Optional

from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener
from app.extensions.werkingsgebieden.service import WerkingsgebiedRelatedObjectService


class RelatedObjectsOnWerkingsgebiedListener(Listener[RetrievedObjectsEvent]):
    TARGET_FIELD: str = "Related_Objects"
    TARGET_SERVICE: str = "computed_fields"

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        if self.TARGET_SERVICE not in event.context.response_model.service_config:
            return event

        fields = event.context.response_model.service_config[self.TARGET_SERVICE]["fields"]
        if not any(field.get("field_name") == self.TARGET_FIELD for field in fields):
            return event

        service = WerkingsgebiedRelatedObjectService(event, self.TARGET_FIELD)
        result_rows = service.process()

        event.payload.rows = result_rows
        return event
