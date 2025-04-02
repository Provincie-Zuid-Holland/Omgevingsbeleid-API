from typing import Dict, List, Type

from pydantic import BaseModel

from app.core.types import Model


class ModelsProvider:
    def __init__(self):
        self._models: Dict[str, Model] = {}

    def add(self, model: Model):
        if model.id in self._models:
            raise ValueError(f"Model with id '{model.id}' already exists.")
        self._models[model.id] = model

    def add_list(self, models: List[Model]):
        for model in models:
            self.add(model)

    def get_model(self, model_id: str) -> Model:
        if model_id not in self._models:
            raise KeyError(f"Model with id '{model_id}' does not exist.")
        return self._models[model_id]

    def get_pydantic_model(self, model_id: str) -> Type[BaseModel]:
        model: Model = self.get_model(model_id)
        return model.pydantic_model
