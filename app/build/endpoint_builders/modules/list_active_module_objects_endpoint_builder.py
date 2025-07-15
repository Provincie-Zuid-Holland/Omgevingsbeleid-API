from typing import List
from app.api.domains.modules.endpoints.list_active_module_objects_endpoint import (
    ActiveModuleObjectsResponse,
    ListActiveModuleObjectsEndpointContext,
    get_list_active_module_objects_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListActiveModuleObjectsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_active_module_objects"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        context = ListActiveModuleObjectsEndpointContext(
            builder_data=builder_data,
            object_type=api.object_type,
        )
        endpoint = self._inject_context(get_list_active_module_objects_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=List[ActiveModuleObjectsResponse],
            summary=f"List the last modified module object grouped per module ID",
            description=None,
            tags=[api.object_type],
        )
