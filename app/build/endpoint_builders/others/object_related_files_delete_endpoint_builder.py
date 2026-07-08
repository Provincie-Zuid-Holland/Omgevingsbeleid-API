from app.api.domains.others.endpoints.object_related_files_delete_endpoint import (
    post_object_related_files_delete_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectRelatedFilesDeleteEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_related_files_delete"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_object_related_files_delete_endpoint,
            methods=["DELETE"],
            summary="Delete a related file",
            response_model=ResponseOK,
            description=None,
            tags=["Object Related Files"],
        )
