from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, validator


class ExecutionStrategy(str, Enum):
    PROPERTY = "property"
    SERVICE = "service"


class ComputedField(BaseModel):
    id: str
    model_id: str  # schema of the value to be computed
    attribute_name: str
    is_list: bool = False
    is_optional: bool = True
    static: bool = False
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SERVICE
    handler_id: Optional[str] = None
    property_callable: Optional[Any] = None  # TODO: Type

    @validator("property_callable")
    def validate_property_callable(cls, v, values):
        if values.get("execution_strategy") == ExecutionStrategy.PROPERTY and not v:
            raise ValueError("property_callable must be provided when execution_strategy is PROPERTY")
        return v

    @validator("handler_id")
    def validate_handler_id(cls, v, values):
        if values.get("execution_strategy") == ExecutionStrategy.SERVICE and not v:
            raise ValueError("handler_id must be provided when execution_strategy is SERVICE")
        return v
