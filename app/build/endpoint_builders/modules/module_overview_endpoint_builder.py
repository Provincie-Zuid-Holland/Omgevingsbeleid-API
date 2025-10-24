from typing import Dict, List

from app.api.domains.modules.endpoints.module_overview_endpoint import (
    view_module_overview_endpoint,
    ViewModuleOverviewEndpointContext,
    ModuleObjectsResponse,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
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
    ) -> ConfiguredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        model_map: Dict[str, str] = resolver_config["model_map"]

        context = ViewModuleOverviewEndpointContext(
            builder_data=builder_data,
            model_map=model_map,
        )
        endpoint = self._inject_context(view_module_overview_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=List[ModuleObjectsResponse],
            summary="Get overview of a module",
            description=None,
            tags=["Modules"],
        )
