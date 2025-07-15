from app.api.domains.modules.endpoints.module_overview_endpoint import ModuleOverview, view_module_overview_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleOverviewEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_overview"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=view_module_overview_endpoint,
            methods=["GET"],
            response_model=ModuleOverview,
            summary=f"Get overview of a module",
            description=None,
            tags=["Modules"],
        )
