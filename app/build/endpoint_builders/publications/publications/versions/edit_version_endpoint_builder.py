from app.api.domains.publications.endpoints.publications.versions.edit_version_endpoint import (
    PublicationVersionEditResponse,
    post_edit_version_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class EditPublicationVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_publication_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_edit_version_endpoint,
            methods=["POST"],
            response_model=PublicationVersionEditResponse,
            summary="Edit an existing publication version",
            description=None,
            tags=["Publication Versions"],
        )
