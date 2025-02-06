from typing import List, Optional

from pydantic import BaseModel

from app.dynamic.event.types import Listener
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.werkingsgebieden.service.join_werkingsgebieden import JoinWerkingsgebiedenService


class RetrievedModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def handle_event(self, event: RetrievedModuleObjectsEvent) -> Optional[RetrievedModuleObjectsEvent]:
        add_service: JoinWerkingsgebiedenService = JoinWerkingsgebiedenService(
            event.get_db(),
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.join_werkingsgebieden()
        event.payload.rows = result_rows

        return event
