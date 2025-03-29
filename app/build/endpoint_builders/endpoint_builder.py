from abc import ABC, abstractmethod

from fastapi import APIRouter


class EndpointBuilder(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def bind_endpoint(
        self,
        # models_resolver: ModelsResolver,
        # endpoint_config: EndpointConfig,
        # api: Api,
        router: APIRouter,
    ):
        pass
