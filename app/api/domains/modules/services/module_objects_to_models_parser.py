from typing import Dict, Type, Any

from pydantic import BaseModel

from app.core.services import ModelsProvider
from app.core.tables.modules import ModuleObjectsTable


class ModuleObjectsToModelsParser:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider = models_provider

    def parse(self, module_object: ModuleObjectsTable, model_map: Dict[str, str]) -> BaseModel:
        model_id = model_map.get(module_object.Object_Type)
        if model_id is None:
            raise RuntimeError(f"Object type {module_object.Object_Type} is not mapped to a model")
        pydantic_model: Type[BaseModel] = self._models_provider.get_pydantic_model(model_id)
        model_instance: BaseModel = pydantic_model.model_validate(module_object)
        return model_instance

    def parse_from_dict(self, object_type: str, object_dict: Dict[str, Any], model_map: Dict[str, str]) -> BaseModel:
        model_id = model_map.get(object_type)
        if model_id is None:
            raise RuntimeError(f"Object type {object_type} is not mapped to a model")
        pydantic_model: Type[BaseModel] = self._models_provider.get_pydantic_model(model_id)
        model_instance: BaseModel = pydantic_model.model_validate(object_dict)
        return model_instance
