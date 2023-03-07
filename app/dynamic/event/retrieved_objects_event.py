from typing import List
from dataclasses import dataclass


from .types import Event
from app.dynamic.config.models import Model


@dataclass
class RetrievedObjectsEventPayload:
    rows: List[dict]


@dataclass
class RetrievedObjectsEventContext:
    endpoint_id: str
    response_model: Model


class RetrievedObjectsEvent(Event):
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
        rows: List[dict],
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
