from app.api.domains.publications.endpoints.publications.reports.act.upload_act_package_report_endpoint import (
    UploadPackageReportResponse,
)
from app.api.domains.publications.endpoints.publications.reports.announcement.upload_announcement_package_report_endpoint import (
    post_upload_announcement_package_report_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class UploadAnnouncementPackageReportEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "upload_publication_announcement_package_report"

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
            endpoint=post_upload_announcement_package_report_endpoint,
            methods=["POST"],
            summary="Record the submission response from lvbb of a publication announcement package",
            response_model=UploadPackageReportResponse,
            description=None,
            tags=["Publication Announcement Reports"],
        )
