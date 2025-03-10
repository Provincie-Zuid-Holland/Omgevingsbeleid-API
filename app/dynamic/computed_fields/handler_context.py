from typing import List, Protocol, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.computed_fields.models import ComputedField
from app.dynamic.config.models import DynamicObjectModel

T = TypeVar("T")


class HandlerContext:
    """used as args for computed field handlers."""

    def __init__(
        self,
        db: Session,
        dynamic_objects: List[BaseModel],
        dynamic_obj_model: DynamicObjectModel,
        computed_field: ComputedField,
    ):
        self.db = db
        self.dynamic_objects = dynamic_objects
        self.dynamic_obj_model = dynamic_obj_model
        self.computed_field = computed_field


class ComputedFieldHandlerCallable(Protocol):
    """type for computed field handlers that use HandlerContext."""

    def __call__(self, context: HandlerContext) -> List[T]: ...
