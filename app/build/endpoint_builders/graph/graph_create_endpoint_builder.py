from app.api.domains.graph.endpoints.graph_create_endpoint import post_graph_create_endpoint
from app.api.domains.modules.endpoints.activate_module_endpoint import post_activate_module_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class GraphCreateEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "graph_create"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_graph_create_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Create graph",
            description=None,
            tags=["Graph"],
        )
