from app.api.domains.publications.endpoints.publications.versions.attachments.upload_attachment_endpoint import (
    UploadAttachmentResponse,
    post_upload_attachment_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class UploadPublicationVersionAttachmentEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "upload_publication_version_attachment"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_upload_attachment_endpoint,
            methods=["POST"],
            summary=f"Upload an attachment for a Publication Version",
            response_model=UploadAttachmentResponse,
            description=None,
            tags=["Publication Versions"],
        )
