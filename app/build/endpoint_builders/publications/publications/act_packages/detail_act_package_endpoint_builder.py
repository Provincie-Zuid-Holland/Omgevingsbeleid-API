from app.api.domains.publications.endpoints.publications.act_packages.detail_act_package_endpoint import (
    get_detail_act_package_endpoint,
    PublicationActPackageDetailResponse,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailActPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_act_package"

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
            endpoint=get_detail_act_package_endpoint,
            methods=["GET"],
            response_model=PublicationActPackageDetailResponse,
            summary="Get details of a publication act package",
            tags=["Publication Act Packages"],
        )
