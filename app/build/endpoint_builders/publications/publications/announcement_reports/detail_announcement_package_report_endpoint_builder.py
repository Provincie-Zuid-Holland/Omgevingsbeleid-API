from app.api.domains.publications.endpoints.publications.announcement_reports.detail_announcement_package_report_endpoint import (
    get_detail_announcement_package_report_endpoint,
)
from app.api.domains.publications.types.models import PublicationAnnouncementPackageReport
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailAnnouncementPackageReportEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_announcement_package_report"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_announcement_package_report_endpoint,
            methods=["GET"],
            response_model=PublicationAnnouncementPackageReport,
            summary="Get details of a publication announcement report",
            description=None,
            tags=["Publication Announcement Reports"],
        )
