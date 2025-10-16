from typing import List, Dict, Type, Union

import pydantic
from pydantic import BaseModel
from pydantic.main import ModelT

from app.core.services import ModelsProvider
from app.core.tables.modules import ModuleObjectsTable


class ModuleObjectsToModelsParser:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider = models_provider

    def cast(self, module_object: ModuleObjectsTable, model_map: Dict[str, str]) -> BaseModel:
        model_id = model_map.get(module_object.Object_Type)
        if model_id is None:
            raise RuntimeError(f"Object type {module_object.Object_Type} is not mapped to a model")
        pydantic_model: Type[BaseModel] = self._models_provider.get_pydantic_model(model_id)
        model_instance: BaseModel = pydantic_model.model_validate(module_object)
        return model_instance

    def get_types(self, model_map: Dict[str, str]) -> List[Type[BaseModel]]:
        result: List[Type[BaseModel]] = []
        for model_id in model_map.values():
            pydantic_model: Type[BaseModel] = self._models_provider.get_pydantic_model(model_id)
            result.append(pydantic_model)
        return result

    @staticmethod
    def update_response_model(name: str, base: ModelT, dynamic_models: List[Type[BaseModel]]) -> Type[ModelT]:
        model_type = Union[tuple(dynamic_models)]

        return pydantic.create_model(name, __base__=base, Model=(model_type, ...))
