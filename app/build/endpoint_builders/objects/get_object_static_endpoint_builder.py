from app.api.domains.objects.endpoints.get_object_static_endpoint import (
    ObjectStaticEndpointContext,
    view_get_object_static_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model


class GetObjectStaticEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "get_object_static"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        response_model: Model = models_provider.get_model(resolver_config["response_model"])

        context = ObjectStaticEndpointContext(
            object_type=api.object_type,
            response_config_model=response_model,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(view_get_object_static_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=response_model.pydantic_model,
            summary=f"Get object static of {api.object_type} by lineage id",
            tags=[api.object_type],
        )
