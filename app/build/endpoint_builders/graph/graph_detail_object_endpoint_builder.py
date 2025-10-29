from app.api.domains.graph.endpoints.graph_detail_object_endpoint import DetailResponse, get_graph_detail_object_endpoint
from app.api.domains.modules.endpoints.activate_module_endpoint import post_activate_module_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class GraphDetailObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "graph_detail_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{object_type}" not in builder_data.path:
            raise RuntimeError("Missing {object_type} argument in path")
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_graph_detail_object_endpoint,
            methods=["GET"],
            response_model=DetailResponse,
            summary="Object in graph",
            description=None,
            tags=["Graph"],
        )
