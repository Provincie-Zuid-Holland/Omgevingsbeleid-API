from app.api.domains.objects.endpoints.acknowledged_relation_edit_endpoint import (
    AcknowledgedRelationEditEndpointContext,
    post_acknowledged_relation_edit_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AcknowledgedRelationEditEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "edit_acknowledged_relation"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        context = AcknowledgedRelationEditEndpointContext(
            object_type=api.object_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(post_acknowledged_relation_edit_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit an acknowledged relation",
            description=None,
            tags=[api.object_type],
        )
