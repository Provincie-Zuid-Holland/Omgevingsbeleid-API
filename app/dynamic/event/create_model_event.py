from collections import OrderedDict
from dataclasses import dataclass

from app.dynamic.computed_field_resolver import ComputedFieldResolver
from app.dynamic.models_resolver import ModelsResolver

from ..config.models import IntermediateModel
from .types import Event


@dataclass
class CreateModelEventPayload:
    pydantic_fields: OrderedDict
    static_pydantic_fields: OrderedDict


@dataclass
class CreateModelEventContext:
    intermediate_model: IntermediateModel
    models_resolver: ModelsResolver
    computed_fields_resolver: ComputedFieldResolver


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
        models_resolver: ModelsResolver,
        computed_fields_resolver: ComputedFieldResolver,
    ):
        return CreateModelEvent(
            payload=CreateModelEventPayload(pydantic_fields, static_pydantic_fields),
            context=CreateModelEventContext(intermediate_model, models_resolver, computed_fields_resolver),
        )
