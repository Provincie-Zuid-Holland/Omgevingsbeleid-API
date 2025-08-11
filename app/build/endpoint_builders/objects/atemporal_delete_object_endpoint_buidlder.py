from app.api.domains.objects.endpoints import AtemporalDeleteObjectEndpointContext, atemporal_delete_object_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AtemporalDeleteObjectEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "atemporal_delete_object"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        context = AtemporalDeleteObjectEndpointContext(
            object_type=api.object_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(atemporal_delete_object_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary="Delete atemporal object",
            tags=[api.object_type],
        )
