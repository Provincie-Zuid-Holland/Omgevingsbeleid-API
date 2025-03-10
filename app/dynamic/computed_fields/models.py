from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, validator


class ComputedField(BaseModel):
    id: str
    model_id: str  # schema of the value to be computed
    attribute_name: str
    is_list: bool = False
    is_optional: bool = True
    static: bool = False


class ServiceComputedField(ComputedField):
    handler_id: str


class PropertyComputedField(ComputedField):
    property_callable: Any
