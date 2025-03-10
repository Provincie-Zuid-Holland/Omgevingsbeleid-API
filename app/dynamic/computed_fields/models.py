from typing import Any

from pydantic import BaseModel


class ComputedField(BaseModel):
    id: str
    model_id: str  # schema of the value to be computed
    attribute_name: str  # field added to the response model
    is_list: bool = False
    is_optional: bool = True
    static: bool = False


class ServiceComputedField(ComputedField):
    handler_id: str


class PropertyComputedField(ComputedField):
    property_callable: Any
