
from app.api.domains.objects.endpoints import view_object_counts_endpoint
from app.api.domains.objects.types import ObjectCountResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectCountsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_counts"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=view_object_counts_endpoint,
            methods=["GET"],
            response_type=ObjectCountResponse,
            summary=f"List object types with counts for loggedin user",
            tags=["Objects"],
        )
