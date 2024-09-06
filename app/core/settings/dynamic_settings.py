from typing import List, Type

from pydantic import BaseSettings, create_model

from .core_settings import CoreSettings


class DynamicSettings(CoreSettings):
    pass


def create_dynamic_settings(settings_classes: List[Type[BaseSettings]] = []) -> DynamicSettings:
    fields = {}
    for ext_cls in settings_classes:
        fields.update({name: (field.outer_type_, field.default) for name, field in ext_cls.__fields__.items()})

    MergedSettings = create_model("MergedSettings", **fields, __base__=CoreSettings)

    result = MergedSettings()
    return result
