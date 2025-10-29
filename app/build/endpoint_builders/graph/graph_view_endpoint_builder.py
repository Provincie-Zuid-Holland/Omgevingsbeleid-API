from app.api.domains.graph.endpoints.graph_view_endpoint import ViewResponse, get_graph_view_endpoint
from app.api.domains.modules.endpoints.activate_module_endpoint import post_activate_module_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class GraphViewEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "graph_view"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_graph_view_endpoint,
            methods=["GET"],
            response_model=ViewResponse,
            summary="View full graph",
            description=None,
            tags=["Graph"],
        )
