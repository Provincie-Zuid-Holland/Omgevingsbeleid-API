from typing import Dict, Tuple, Type, Union, get_type_hints

from pydantic import BaseModel, create_model

from app.api.domains.modules.types import TModel
from app.core.services import ModelsProvider


class ModelDynamicTypeBuilder:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider: ModelsProvider = models_provider

    def build_object_union_type(self, model_map: Dict[str, str]) -> Union[BaseModel]:
        model_types: Tuple[Type[BaseModel], ...] = tuple(
            self._models_provider.get_pydantic_model(model_id) for model_id in model_map.values()
        )
        return Union[model_types]

    def merge_union_models(self, union_type: Union[BaseModel], model_name: str) -> type[TModel]:
        models = union_type.__args__
        fields = {}

        for model in models:
            annotations = get_type_hints(model)
            for annotation_name, annotation_type in annotations.items():
                if annotation_name not in fields:
                    default = getattr(model, annotation_name, ...)
                    fields[annotation_name] = (annotation_type, default)

        return create_model(model_name, **fields)
