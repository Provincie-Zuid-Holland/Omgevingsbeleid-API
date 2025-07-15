from app.api.domains.publications.endpoints.publications.act_reports.download_act_package_report_endpoint import (
    get_download_act_package_report_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DownloadActPackageReportEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "download_publication_act_package_report"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{act_report_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {act_report_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_download_act_package_report_endpoint,
            methods=["GET"],
            summary="Download publication package report",
            description=None,
            tags=["Publication Act Reports"],
            response_model=None,
        )
