from typing import List, Dict, Type, Union

import pydantic
from pydantic import BaseModel
from pydantic.main import ModelT

from app.core.services import ModelsProvider


class ModelDynamicTypeEnricher:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider = models_provider

    def enrich(self, model_name: str, base_model: ModelT, model_map: Dict[str, str]) -> Type[ModelT]:
        dynamic_types: List[Type[BaseModel]] = []
        for model_id in model_map.values():
            pydantic_model: Type[BaseModel] = self._models_provider.get_pydantic_model(model_id)
            dynamic_types.append(pydantic_model)
        model_type = Union[tuple(dynamic_types)]
        return pydantic.create_model(model_name, __base__=base_model, Model=(model_type, ...))
