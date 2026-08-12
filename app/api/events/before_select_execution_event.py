from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select

from app.api.events.types import ApiEvent
from app.core.types import Model


@dataclass
class BeforeSelectExecutionEventPayload:
    query: Select


@dataclass
class BeforeSelectExecutionEventContext:
    response_model: Model | None
    objects_table_ref: Any | None


class BeforeSelectExecutionEvent(ApiEvent):
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
        response_model: Model | None = None,
        objects_table_ref: Any | None = None,
    ):
        return BeforeSelectExecutionEvent(
            payload=BeforeSelectExecutionEventPayload(query),
            context=BeforeSelectExecutionEventContext(
                response_model=response_model,
                objects_table_ref=objects_table_ref,
            ),
        )
