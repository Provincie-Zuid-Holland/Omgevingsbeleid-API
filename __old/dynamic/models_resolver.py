from typing import Dict

from .config.models import Model


class ModelsResolver:
    def __init__(self):
        self._models: Dict[str, Model] = {}

    def get(self, id: str) -> Model:
        if not id in self._models:
            raise RuntimeError(f"Model ID '{id}' does not exist")

        return self._models[id]

    def exists(self, id: str) -> bool:
        return id in self._models

    def add(self, model: Model):
        if model.id in self._models:
            raise RuntimeError(f"Model ID '{id}' already exists")

        self._models[model.id] = model
