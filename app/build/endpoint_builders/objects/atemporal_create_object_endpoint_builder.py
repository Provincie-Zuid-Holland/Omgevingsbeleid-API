
from typing import Type

from pydantic import BaseModel
from app.api.domains.objects.endpoints import AtemporalCreateObjectEndpointContext, atemporal_create_object_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AtemporalCreateObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "atemporal_create_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data

        request_type: Type[BaseModel] = models_provider.get_pydantic_model(resolver_config["request_model"])
        response_type: Type[BaseModel] = models_provider.get_pydantic_model(resolver_config["response_model"])

        context = AtemporalCreateObjectEndpointContext(
            object_type=api.object_type,
            request_type=request_type,
            response_type=response_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(atemporal_create_object_endpoint, context)
        endpoint = self._overwrite_argument_type(endpoint, "object_in", request_type)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_type=response_type,
            summary=f"Add new object",
            tags=[api.object_type],
        )
