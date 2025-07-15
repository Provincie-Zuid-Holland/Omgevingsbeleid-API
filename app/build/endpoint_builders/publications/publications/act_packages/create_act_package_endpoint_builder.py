from app.api.domains.publications.endpoints.publications.act_packages.create_act_package_endpoint import (
    PublicationPackageCreatedResponse,
    post_create_act_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreatePublicationPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_act_package"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_act_package_endpoint,
            methods=["POST"],
            response_model=PublicationPackageCreatedResponse,
            summary="Create new Publication Act Package",
            tags=["Publication Act Packages"],
        )
