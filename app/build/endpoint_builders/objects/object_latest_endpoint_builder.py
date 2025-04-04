from typing import Type
from pydantic import BaseModel

from app.api.domains.objects.endpoints.object_latest_endpoint import ObjectLatestEndpointContext, view_object_latest_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectLatestEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_latest"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{lineage_id}" in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        response_model: Type[BaseModel] = models_provider.get_pydantic_model(resolver_config["response_model"])

        context: ObjectLatestEndpointContext = ObjectLatestEndpointContext(
            object_type=api.object_type,
            response_model=response_model,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(view_object_latest_endpoint, context=context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_type=response_model,
            summary=f"View latest valid record for an {api.object_type} lineage id",
            tags=[api.object_type],
        )
