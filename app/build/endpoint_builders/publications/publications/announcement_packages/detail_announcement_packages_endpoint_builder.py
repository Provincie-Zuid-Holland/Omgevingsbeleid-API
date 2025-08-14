from app.api.domains.publications.endpoints.publications.announcement_packages.detail_announcement_package_endpoint import (
    PublicationAnnouncementPackageDetailItem,
    get_detail_announcement_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailAnnouncementPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_announcement_package"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{announcement_package_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {announcement_package_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_announcement_package_endpoint,
            methods=["GET"],
            response_model=PublicationAnnouncementPackageDetailItem,
            summary="Get detailed information about a specific announcement publication package",
            description=None,
            tags=["Publication Announcement Packages"],
        )
