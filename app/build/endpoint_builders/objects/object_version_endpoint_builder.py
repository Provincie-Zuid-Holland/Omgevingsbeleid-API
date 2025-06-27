from app.api.domains.objects.endpoints.object_version_endpoint import (
    ObjectVersionEndpointContext,
    view_object_version_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class ObjectVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{object_uuid}" in builder_data.path:
            raise RuntimeError("Missing {object_uuid} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        response_model: Model = models_provider.get_model(resolver_config["response_model"])

        context = ObjectVersionEndpointContext(
            object_type=api.object_type,
            response_config_model=response_model,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(view_object_version_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=response_model.pydantic_model,
            summary=f"Get specific {api.object_type} by uuid",
            tags=[api.object_type],
        )
