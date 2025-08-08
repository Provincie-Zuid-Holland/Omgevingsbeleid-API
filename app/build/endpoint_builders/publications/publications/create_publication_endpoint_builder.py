from app.api.domains.publications.endpoints.publications.create_publication_endpoint import (
    PublicationCreatedResponse,
    post_create_publication_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_publication_endpoint,
            methods=["POST"],
            response_model=PublicationCreatedResponse,
            summary="Create a new publication",
            tags=["Publications"],
        )
