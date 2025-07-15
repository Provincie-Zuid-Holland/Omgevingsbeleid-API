from app.api.domains.others.endpoints.files_upload_endpoint import UploadFileResponse, post_files_upload_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class StorageFileUploadFileEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "storage_file_upload_file"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_files_upload_endpoint,
            methods=["POST"],
            summary="Upload an File",
            response_model=UploadFileResponse,
            description=None,
            tags=["Storage File"],
        )
