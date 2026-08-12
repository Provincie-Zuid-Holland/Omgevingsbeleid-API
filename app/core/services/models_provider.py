from pydantic import BaseModel

from app.core.types import DynamicObjectModel, Model


class ModelsProvider:
    def __init__(self):
        self._models: dict[str, Model | DynamicObjectModel] = {}

    def add(self, model: Model | DynamicObjectModel):
        if model.id in self._models:
            raise ValueError(f"Model with id '{model.id}' already exists.")
        self._models[model.id] = model

    def add_list(self, models: list[Model | DynamicObjectModel]):
        for model in models:
            self.add(model)

    def get_model(self, model_id: str) -> Model | DynamicObjectModel:
        if model_id not in self._models:
            raise KeyError(f"Model with id '{model_id}' does not exist.")
        return self._models[model_id]

    def get_pydantic_model(self, model_id: str) -> type[BaseModel]:
        model: Model | DynamicObjectModel = self.get_model(model_id)
        return model.pydantic_model

    def exists(self, model_id: str) -> bool:
        return model_id in self._models
