from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


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
    execution_strategy: ExecutionStrategy = ExecutionStrategy.PROPERTY
    handler_id: Optional[str] = None
    property_callable: Optional[Any] = None  # TODO: Type
