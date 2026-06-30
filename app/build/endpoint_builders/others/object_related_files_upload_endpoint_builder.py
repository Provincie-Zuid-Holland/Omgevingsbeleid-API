from app.api.domains.others.endpoints.object_related_files_upload_endpoint import (
    post_object_related_files_upload_endpoint,
)
from app.api.domains.others.types import ObjectRelatedFileResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ObjectRelatedFilesUploadEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_related_files_upload"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_object_related_files_upload_endpoint,
            methods=["POST"],
            summary="Upload and link a file to an object",
            response_model=ObjectRelatedFileResponse,
            description=None,
            tags=["Object Related Files"],
        )
