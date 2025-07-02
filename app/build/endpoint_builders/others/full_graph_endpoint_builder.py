from typing import List
from app.api.domains.modules.endpoints.module_list_statuses_endpoint import view_module_list_statuses_endpoint
from app.api.domains.modules.types import ModuleStatus
from app.api.domains.others.endpoints.full_graph_endpoint import get_full_graph_endpoint
from app.api.domains.others.types import GraphResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider






class FullGraphEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "full_graph"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_full_graph_endpoint,
            methods=["GET"],
            response_model=GraphResponse,
            summary=f"A graph representation",
            description=None,
            tags=["Graph"],
        )
