from app.api.domains.publications.endpoints.publications.act_packages.validate_act_package_endpoint import (
    get_validate_act_package_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ValidatePublicationPackageEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "validate_publication_act_package"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{version_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_validate_act_package_endpoint,
            methods=["GET"],
            response_model=ResponseOK,
            summary="Validate Publication Act Package",
            tags=["Publication Act Packages"],
        )
