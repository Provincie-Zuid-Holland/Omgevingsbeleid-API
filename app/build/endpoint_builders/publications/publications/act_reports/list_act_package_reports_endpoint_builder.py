from app.api.domains.publications.endpoints.publications.act_reports.list_act_package_reports_endpoint import (
    get_list_act_package_reports_endpoint,
)
from app.api.domains.publications.types.models import PublicationActPackageReportShort
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListActPackageReportsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_act_package_reports"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_act_package_reports_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationActPackageReportShort],
            summary="List the existing Publication Act reports",
            description=None,
            tags=["Publication Act Reports"],
        )
