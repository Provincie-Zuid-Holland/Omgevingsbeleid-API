from typing import List
from dataclasses import dataclass

from app.dynamic.config.models import Model
from app.dynamic.event.types import Event


@dataclass
class RetrievedModuleObjectsEventPayload:
    rows: List[dict]


@dataclass
class RetrievedModuleObjectsEventContext:
    endpoint_id: str
    response_model: Model


class RetrievedModuleObjectsEvent(Event):
    def __init__(
        self,
        payload: RetrievedModuleObjectsEventPayload,
        context: RetrievedModuleObjectsEventContext,
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
        return RetrievedModuleObjectsEvent(
            payload=RetrievedModuleObjectsEventPayload(rows),
            context=RetrievedModuleObjectsEventContext(
                endpoint_id,
                response_model,
            ),
        )
