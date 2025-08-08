from app.api.domains.publications.endpoints.publications.versions.create_version_endpoint import (
    PublicationVersionCreatedResponse,
    post_create_version_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{publication_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_version_endpoint,
            methods=["POST"],
            response_model=PublicationVersionCreatedResponse,
            summary="Create new publication version",
            tags=["Publication Versions"],
        )
