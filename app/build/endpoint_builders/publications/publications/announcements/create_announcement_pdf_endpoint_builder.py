from app.api.domains.publications.endpoints.publications.announcements.create_announcement_pdf_endpoint import (
    post_create_announcement_pdf_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreateAnnouncementPdfEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_announcement_pdf"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{announcement_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {announcement_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_announcement_pdf_endpoint,
            methods=["POST"],
            response_model=None,
            summary="Download Announcement as Pdf",
            tags=["Publication Announcements"],
        )
