from typing import List
from app.api.domains.objects.endpoints.acknowledged_relation_list_endpoint import (
    AcknowledgedRelationListEndpointContext,
    get_acknowledged_relation_list_endpoint,
)
from app.api.domains.objects.endpoints.types import AcknowledgedRelation
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class AcknowledgedRelationListEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_acknowledged_relations"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{lineage_id}" in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        context = AcknowledgedRelationListEndpointContext(
            object_type=api.object_type,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_acknowledged_relation_list_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=List[AcknowledgedRelation],
            summary=f"Get all acknowledged relations of the given {api.object_type} lineage",
            description=None,
            tags=[api.object_type],
        )
