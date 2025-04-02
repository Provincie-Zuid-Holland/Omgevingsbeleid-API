from abc import ABC, abstractmethod
from enum import Enum
import functools
import inspect
from typing import Callable, List, Optional, Type, Union

from pydantic import BaseModel, Field

from app.api.endpoint import EndpointContextBuilderData
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.models_provider import ModelsProvider


# Used to give data to fastapi.add_api_route
# @see: site-packages/fastapi/routing.py def add_api_route
class ConfiguiredFastapiEndpoint(BaseModel):
    path: str
    endpoint: Callable
    methods: list[str]
    response_type: Union[Type[BaseModel], type]
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: List[Union[str, Enum]] = Field(default_factory=list)


class EndpointBuilder(ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        pass

    def _inject_context(self, endpoint: Callable, context: BaseModel) -> Callable:
        """
        Injects a context object into the given endpoint function by creating a partial
        function with the context pre-filled. The resulting function will have its
        signature adjusted to exclude the "context" parameter.

        This will allow the endpoint to be called without explicitly passing the
        context parameter, while still having access to it.

        This in turn will make sure that FastAPI / OpenAPI will not include the context
        parameter in the generated API documentation.

        Args:
            endpoint (Callable): The original endpoint function to which the context
                will be injected.
            context (BaseModel): The context object to be injected into the endpoint.
        Returns:
            Callable: A new function with the context pre-filled and the "context"
                parameter removed from its signature.
        """
        partial_func = functools.partial(endpoint, context=context)
        functools.update_wrapper(partial_func, endpoint)
        
        # Adjust the signature to remove the "context" parameter.
        original_sig = inspect.signature(endpoint)
        new_params = [
            param for name, param in original_sig.parameters.items()
            if name != "context"
        ]

        new_sig = original_sig.replace(parameters=new_params)
        partial_func.__signature__ = new_sig

        return partial_func
