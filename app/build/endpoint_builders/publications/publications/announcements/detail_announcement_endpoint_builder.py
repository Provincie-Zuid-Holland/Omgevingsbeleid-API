from app.api.domains.publications.endpoints.publications.announcements.detail_announcement_endpoint import (
    get_detail_announcement_endpoint,
)
from app.api.domains.publications.types.models import PublicationAnnouncement
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationAnnouncementEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_announcement"

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
            endpoint=get_detail_announcement_endpoint,
            methods=["GET"],
            response_model=PublicationAnnouncement,
            summary="Get details of a publication announcement",
            description=None,
            tags=["Publication Announcements"],
        )
