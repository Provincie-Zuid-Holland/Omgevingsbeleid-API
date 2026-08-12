from dataclasses import dataclass

from pydantic import BaseModel

from app.api.events.types import ApiEvent
from app.core.types import Model


@dataclass
class RetrievedObjectsEventPayload:
    rows: list[BaseModel]


@dataclass
class RetrievedObjectsEventContext:
    endpoint_id: str
    response_model: Model


class RetrievedObjectsEvent(ApiEvent):
    def __init__(
        self,
        payload: RetrievedObjectsEventPayload,
        context: RetrievedObjectsEventContext,
    ):
        super().__init__()
        self.payload = payload
        self.context = context

    @staticmethod
    def create(
        rows: list[BaseModel],
        endpoint_id: str,
        response_model: Model,
    ):
        return RetrievedObjectsEvent(
            payload=RetrievedObjectsEventPayload(rows),
            context=RetrievedObjectsEventContext(
                endpoint_id,
                response_model,
            ),
        )
