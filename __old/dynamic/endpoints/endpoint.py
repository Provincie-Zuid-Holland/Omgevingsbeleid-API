from abc import ABC, abstractmethod

from fastapi import APIRouter

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.models_resolver import ModelsResolver


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
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        pass
