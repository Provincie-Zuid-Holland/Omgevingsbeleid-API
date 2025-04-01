from typing import Dict, List

from app.build.endpoint_builders.endpoint_builder import EndpointBuilder
from app.build.objects.types import Model


class ModelProvider:
    def __init__(self, models: List[Model]):
        self._models: Dict[str, Model] = {
            m.id: m for m in models
        }

    def get(self, model_id: str) -> Model:
        if model_id not in self._models:
            raise KeyError(f"Model with id '{model_id}' does not exist.")
        return self._models[model_id]
