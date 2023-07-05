from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import Select

from app.dynamic.config.models import Model

from .types import Event


@dataclass
class BeforeSelectExecutionEventPayload:
    query: Select


@dataclass
class BeforeSelectExecutionEventContext:
    response_model: Optional[Model]
    objects_table_ref: Optional[Any]


class BeforeSelectExecutionEvent(Event):
    def __init__(
        self,
        payload: BeforeSelectExecutionEventPayload,
        context: BeforeSelectExecutionEventContext,
    ):
        super().__init__()
        self.payload = payload
        self.context = context

    @staticmethod
    def create(
        query: Select,
        response_model: Optional[Model] = None,
        objects_table_ref: Optional[Any] = None,
    ):
        return BeforeSelectExecutionEvent(
            payload=BeforeSelectExecutionEventPayload(query),
            context=BeforeSelectExecutionEventContext(
                response_model=response_model,
                objects_table_ref=objects_table_ref,
            ),
        )
