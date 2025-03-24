from typing import Any, Dict, Type

from pydantic import BaseModel


class ModelParserContextResolver:
    def __init__(self, **kwargs):
        self._context = kwargs


ModelParserContext = Dict[str, Any]


class ModelParser:
    def __init__(self, context: ModelParserContext):
        self._context = context

    def parse(self, model_type: Type[BaseModel], data: Any) -> BaseModel:
        return model_type.model_validate(data, context=self._context)
