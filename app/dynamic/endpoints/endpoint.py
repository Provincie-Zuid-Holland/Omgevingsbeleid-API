from abc import ABC, abstractmethod

from fastapi import APIRouter

from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.config.models import EndpointConfig


class Endpoint(ABC):
    @abstractmethod
    def register(self, router: APIRouter) -> APIRouter:
        pass


class EndpointResolver(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
    ) -> Endpoint:
        pass
