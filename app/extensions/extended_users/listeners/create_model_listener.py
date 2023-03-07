from typing import List, Optional

from app.dynamic.event.types import Listener
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.config.models import Model


class CreateModelListener(Listener[CreateModelEvent]):
    def handle_event(self, event: CreateModelEvent) -> CreateModelEvent:
        service_config: dict = event.context.intermediate_model.service_config
        if not "extended_user" in service_config:
            return event

        config: dict = service_config.get("extended_user")
        fields_map_config: List[dict] = config.get("fields_map")

        for field_map in fields_map_config:
            field_name: str = field_map.get("to_field")
            model_id: str = field_map.get("model_id")
            model: Model = event.context.models_resolver.get(model_id)

            event.payload.pydantic_fields[field_name] = (
                Optional[model.pydantic_model],
                None,
            )

        return event
