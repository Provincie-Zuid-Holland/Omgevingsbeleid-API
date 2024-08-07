from typing import List, Type

import pydantic

pydantic
from .base_settings import BaseSettings


class DynamicSettings(BaseSettings):
    pass


def extend_settings(classes: List[Type[pydantic.BaseSettings]]):
    for classx in classes:
        for field in classx.__fields__:
            setattr(DynamicSettings, field, classx.__fields__[field])


def dynamic_settings_factory() -> DynamicSettings:
    return DynamicSettings()
