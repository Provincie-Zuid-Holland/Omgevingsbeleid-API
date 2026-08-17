from app.api.domains.publications.endpoints.publications.versions.attachments.download_attachment_endpoint import (
    get_download_attachment_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DownloadPublicationVersionAttachmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "download_publication_version_attachment"

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
            endpoint=get_download_attachment_endpoint,
            methods=["GET"],
            summary="Download a publication version attachment",
            response_model=None,
            tags=["Publication Versions"],
        )
