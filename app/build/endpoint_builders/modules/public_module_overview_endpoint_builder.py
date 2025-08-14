from app.api.domains.modules.endpoints.public_module_overview_endpoint import (
    PublicModuleOverview,
    get_public_module_overview_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class PublicModuleOverviewEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "public_module_overview"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_public_module_overview_endpoint,
            methods=["GET"],
            response_model=PublicModuleOverview,
            summary="Get overview of a public module",
            description=None,
            tags=["Public Modules"],
        )
