from app.api.domains.publications.endpoints.publications.announcements.create_announcement_endpoint import (
    AnnouncementCreatedResponse,
    post_create_announcement_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationAnnouncementEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_announcement"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{act_package_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {act_package_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_announcement_endpoint,
            methods=["POST"],
            response_model=AnnouncementCreatedResponse,
            summary="Create new publication announcement",
            description=None,
            tags=["Publication Announcements"],
        )
