
from app.api.domains.others.endpoints.object_graph_endpoint import GraphIterationsConfig, ObjectGraphEndpointContext, get_object_graph_endpoint
from app.api.domains.others.types import GraphResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectGraphEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_graph"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        graph_iterations = GraphIterationsConfig.model_validate(resolver_config.get("graph_iterations"))

        context = ObjectGraphEndpointContext(
            graph_iterations=graph_iterations,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_object_graph_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=GraphResponse,
            summary=f"A graph representation of an object",
            description=None,
            tags=["Graph"],
        )
