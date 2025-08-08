from app.api.domains.publications.endpoints.publications.announcement_reports.list_announcement_package_reports_endpoint import (
    get_list_annnouncement_package_reports_endpoint,
)
from app.api.domains.publications.types.models import PublicationAnnouncementPackageReportShort
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListAnnouncementPackageReportsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_announcement_package_reports"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_annnouncement_package_reports_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationAnnouncementPackageReportShort],
            summary="List the existing Publication Announcement reports",
            description=None,
            tags=["Publication Announcement Reports"],
        )
