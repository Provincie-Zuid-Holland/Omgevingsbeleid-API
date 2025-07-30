from app.api.domains.publications.endpoints.publications.packages.act.download_act_package_endpoint import (
    get_download_act_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DownloadPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "download_publication_act_package"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{act_package_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {act_package_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_download_act_package_endpoint,
            methods=["GET"],
            summary="Download a generated publication act package ZIP file",
            description=None,
            tags=["Publication Act Packages"],
            response_model=None,
        )
