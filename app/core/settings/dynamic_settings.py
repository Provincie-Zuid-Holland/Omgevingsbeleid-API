from typing import List, Type

from pydantic import create_model
from pydantic_settings import BaseSettings

from .core_settings import CoreSettings


class DynamicSettings(CoreSettings):
    pass


def create_dynamic_settings(settings_classes: List[Type[BaseSettings]] = []) -> DynamicSettings:
    fields = {}
    for ext_cls in settings_classes:
        # In v2 use `field.annotation` to get the field’s type instead of `outer_type_`
        fields.update({name: (field.annotation, field.default) for name, field in ext_cls.model_fields.items()})

    MergedSettings = create_model("MergedSettings", **fields, __base__=CoreSettings)
    result = MergedSettings()
    return result
