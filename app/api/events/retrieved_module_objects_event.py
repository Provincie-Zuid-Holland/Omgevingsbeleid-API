from dataclasses import dataclass

from pydantic import BaseModel

from app.api.events.types import ApiEvent
from app.core.types import Model


@dataclass
class RetrievedModuleObjectsEventPayload:
    rows: list[BaseModel]


@dataclass
class RetrievedModuleObjectsEventContext:
    endpoint_id: str
    response_model: Model


class RetrievedModuleObjectsEvent(ApiEvent):
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
        rows: list[BaseModel],
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
