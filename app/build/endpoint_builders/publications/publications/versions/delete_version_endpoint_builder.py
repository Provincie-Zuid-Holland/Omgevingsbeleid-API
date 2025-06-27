from app.api.domains.publications.endpoints.publications.versions.delete_version_endpoint import (
    post_delete_version_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DeletePublicationVersionEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "delete_publication_version"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{version_uuid}" in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_delete_version_endpoint,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary="Mark a publication version as deleted",
            description="Marks a publication version as deleted.",
            tags=["Publication Versions"],
        )
