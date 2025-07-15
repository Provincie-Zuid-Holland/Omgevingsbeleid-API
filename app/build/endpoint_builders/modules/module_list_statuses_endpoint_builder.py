from typing import List
from app.api.domains.modules.endpoints.module_list_statuses_endpoint import view_module_list_statuses_endpoint
from app.api.domains.modules.types import ModuleStatus
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ModuleListStatusesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "module_list_statuses"

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
            endpoint=view_module_list_statuses_endpoint,
            methods=["GET"],
            response_model=List[ModuleStatus],
            summary="Get status history of the module",
            description=None,
            tags=["Modules"],
        )
