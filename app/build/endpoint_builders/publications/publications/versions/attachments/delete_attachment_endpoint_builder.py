from app.api.domains.publications.endpoints.publications.versions.attachments.delete_attachment_endpoint import (
    post_delete_attachment_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DeletePublicationVersionAttachmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "delete_publication_version_attachment"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")
        if "{attachment_id}" not in builder_data.path:
            raise RuntimeError("Missing {attachment_id} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_delete_attachment_endpoint,
            methods=["DELETE"],
            summary="Delete a publication version attachment",
            response_model=ResponseOK,
            tags=["Publication Versions"],
        )
