from app.api.domains.publications.endpoints.publications.act_reports.detail_act_package_report_endpoint import (
    get_detail_act_package_report_endpoint,
)
from app.api.domains.publications.types.models import PublicationActPackageReport
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailActPackageReportEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_act_package_report"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{act_report_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {act_report_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_act_package_report_endpoint,
            methods=["GET"],
            response_model=PublicationActPackageReport,
            summary="Get details of a publication report",
            description=None,
            tags=["Publication Act Reports"],
        )
