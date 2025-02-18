from typing import Optional

from app.dynamic.config.models import Model
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event.types import Listener
from app.dynamic.models_resolver import ModelsResolver


class CreateModelListener(Listener[CreateModelEvent]):
    def __init__(self, models_resolver: ModelsResolver):
        self._models_resolver: ModelsResolver = models_resolver

    def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "join_werkingsgebieden" in service_config:
            return event

        config: dict = service_config.get("join_werkingsgebieden")
        field_name: str = config.get("to_field")
        model_id: str = config.get("model_id")
        target_object_model: Model = self._models_resolver.get(model_id)

        final_model: Model = target_object_model
        event.payload.pydantic_fields[field_name] = (
            Optional[final_model.pydantic_model],
            None,
        )

        return event
