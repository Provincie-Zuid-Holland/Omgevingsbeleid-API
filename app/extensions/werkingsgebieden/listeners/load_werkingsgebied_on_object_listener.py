from typing import List, Optional

from pydantic import BaseModel

from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener
from app.extensions.werkingsgebieden.service.join_werkingsgebieden import JoinWerkingsgebiedenService


class LoadWerkingsgebiedOnObjectsListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        add_service: JoinWerkingsgebiedenService = JoinWerkingsgebiedenService(
            event.get_db(),
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event
