from typing import Any, Dict, Tuple, Type, Union

from pydantic import BaseModel

from app.core.services import ModelsProvider


class ModelDynamicTypeEnricher:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider: ModelsProvider = models_provider

    def build_object_union_type(self, model_map: Dict[str, str]) -> Any:
        model_types: Tuple[Type[BaseModel], ...] = tuple(
            self._models_provider.get_pydantic_model(model_id) for model_id in model_map.values()
        )
        return Union[model_types]
