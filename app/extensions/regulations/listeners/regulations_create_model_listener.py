from typing import List

from app.dynamic.event.types import Listener
from app.dynamic.event.create_model_event import CreateModelEvent
from app.extensions.regulations.models.models import RegulationShort


class RegulationsCreateModelListener(Listener[CreateModelEvent]):
    def handle_event(self, event: CreateModelEvent) -> CreateModelEvent:
        service_config: dict = event.context.intermediate_model.service_config
        if not "regulations" in service_config:
            return event

        config: dict = service_config.get("regulations")
        field_name: str = config.get("to_field")

        event.payload.pydantic_fields[field_name] = (List[RegulationShort], [])

        return event
