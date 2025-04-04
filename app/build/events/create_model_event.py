from collections import OrderedDict
from dataclasses import dataclass

from app.build.objects.types import IntermediateModel
from app.core.services.models_provider import ModelsProvider
from app.core.services.event.types import Event


@dataclass
class CreateModelEventPayload:
    pydantic_fields: OrderedDict
    static_pydantic_fields: OrderedDict


@dataclass
class CreateModelEventContext:
    intermediate_model: IntermediateModel
    models_provider: ModelsProvider


class CreateModelEvent(Event):
    def __init__(
        self,
        payload: CreateModelEventPayload,
        context: CreateModelEventContext,
    ):
        super().__init__()
        self.payload = payload
        self.context = context

    @staticmethod
    def create(
        pydantic_fields: OrderedDict,
        static_pydantic_fields: OrderedDict,
        intermediate_model: IntermediateModel,
        models_provider: ModelsProvider,
    ):
        return CreateModelEvent(
            payload=CreateModelEventPayload(pydantic_fields, static_pydantic_fields),
            context=CreateModelEventContext(intermediate_model, models_provider),
        )
