from typing import List, Optional

import pydantic

from app.dynamic.config.models import ExtensionModel, Model
from app.dynamic.event.create_model_event import CreateModelEvent
from app.dynamic.event.types import Listener
from app.dynamic.models_resolver import ModelsResolver


class CreateModelListener(Listener[CreateModelEvent]):
    def __init__(self, models_resolver: ModelsResolver):
        self._models_resolver: ModelsResolver = models_resolver
        self._relation_model_id: str = "read_relation_short"

    def handle_event(self, event: CreateModelEvent) -> Optional[CreateModelEvent]:
        service_config: dict = event.context.intermediate_model.service_config
        if not "relations" in service_config:
            return event

        config: dict = service_config.get("relations")
        objects_config: List[dict] = config.get("objects")
        for object_config in objects_config:
            field_name: str = object_config.get("to_field")
            model_id: str = object_config.get("model_id")
            target_object_model: Model = self._models_resolver.get(model_id)

            final_model: Model = target_object_model
            if object_config.get("wrapped_with_relation_data", False):
                final_model: Model = self._get_wrapper_model(final_model)

            event.payload.pydantic_fields[field_name] = (
                List[final_model.pydantic_model],
                [],
            )

        return event

    def _get_wrapper_model(self, target_model: Model) -> Model:
        wrapper_model_id: str = f"{self._relation_model_id}:{target_model.id}"

        wrapper_model_exists: bool = self._models_resolver.exists(wrapper_model_id)
        if not wrapper_model_exists:
            self._generate_relation_wrapper_model(
                wrapper_model_id,
                target_model,
            )

        wrapper_model: Model = self._models_resolver.get(wrapper_model_id)
        return wrapper_model

    def _generate_relation_wrapper_model(self, id: str, target_model: Model):
        relation_model: Model = self._models_resolver.get(self._relation_model_id)
        name: str = f"{relation_model.name}-{target_model.name}"

        wrapper_model: Model = ExtensionModel(
            id=id,
            name=name,
            pydantic_model=pydantic.create_model(
                name,
                **{
                    "Relation": (relation_model.pydantic_model, pydantic.Field()),
                    "Object": (target_model.pydantic_model, pydantic.Field()),
                },
            ),
        )

        self._models_resolver.add(wrapper_model)
