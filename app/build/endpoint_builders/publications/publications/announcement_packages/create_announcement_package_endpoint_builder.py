from app.api.domains.publications.endpoints.publications.announcement_packages.create_announcement_package_endpoint import (
    PublicationAnnouncementPackageCreatedResponse,
    post_create_announcement_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationAnnouncementPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_announcement_package"

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
            endpoint=post_create_announcement_package_endpoint,
            methods=["POST"],
            response_model=PublicationAnnouncementPackageCreatedResponse,
            summary="Create new Publication Announcement Package",
            tags=["Publication Announcement Packages"],
        )
