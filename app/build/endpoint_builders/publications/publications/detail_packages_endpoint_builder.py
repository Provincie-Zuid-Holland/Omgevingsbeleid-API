from app.api.domains.publications.endpoints.publications.packages.detail_package_endpoint import (
    PublicationPackageDetailItem,
    get_detail_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_package"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{package_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {package_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_package_endpoint,
            methods=["GET"],
            response_model=PublicationPackageDetailItem,
            summary="Get detailed information about a specific publication package",
            description=None,
            tags=["Publication Packages"],
        )
