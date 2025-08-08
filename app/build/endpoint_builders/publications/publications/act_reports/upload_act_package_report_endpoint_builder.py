from app.api.domains.publications.endpoints.publications.act_reports.upload_act_package_report_endpoint import (
    post_upload_act_package_report_endpoint,
)
from app.api.domains.publications.endpoints.publications.announcement_reports.upload_announcement_package_report_endpoint import (
    UploadPackageReportResponse,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class UploadActPackageReportEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "upload_publication_act_package_report"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{act_package_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {act_package_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_upload_act_package_report_endpoint,
            methods=["POST"],
            summary="Record the submission response from lvbb of a publication package",
            response_model=UploadPackageReportResponse,
            description=None,
            tags=["Publication Act Reports"],
        )
