from app.api.domains.publications.endpoints.environments.create_environment_endpoint import (
    EnvironmentCreatedResponse,
    post_create_environment_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationEnvironmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_environment"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_environment_endpoint,
            methods=["POST"],
            response_model=EnvironmentCreatedResponse,
            summary="Create new publication environment",
            description=None,
            tags=["Publication Environments"],
        )
