from typing import List

from app.dynamic.event.types import Listener
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.config.models import Model


class MultipleCreateModelListener(Listener[CreateModelEvent]):
    def handle_event(self, event: CreateModelEvent) -> CreateModelEvent:
        service_config: dict = event.context.intermediate_model.service_config
        if not "werkingsgebieden" in service_config:
            return event

        config: dict = service_config.get("werkingsgebieden")
        field_name: str = config.get("to_field")
        model_id: str = config.get("model_id")
        model: Model = event.context.models_resolver.get(model_id)

        event.payload.pydantic_fields[field_name] = (List[model.pydantic_model], [])

        return event
