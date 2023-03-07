from typing import List

from app.dynamic.config.models import IntermediateObject, IntermediateModel
from app.dynamic.event_dispatcher import EventDispatcher, main_event_dispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.validators.validator_provider import ValidatorProvider


class ServiceContainer:
    def __init__(self):
        # @todo: not sure if they need to stay here or moved to dynamic_app builder
        self.build_object_intermediates: List[IntermediateObject] = []
        self.build_model_intermediates: List[IntermediateModel] = []

        self.models_resolver: ModelsResolver = ModelsResolver()
        self.event_dispatcher: EventDispatcher = main_event_dispatcher
        self.converter: Converter = Converter()
        self.validator_provider: ValidatorProvider = ValidatorProvider()
