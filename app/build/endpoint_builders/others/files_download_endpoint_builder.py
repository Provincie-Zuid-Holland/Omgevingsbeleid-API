from app.api.domains.others.endpoints import get_files_download_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import EndpointBuilder, ConfiguredFastapiEndpoint
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services import ModelsProvider


class DownloadStorageFilesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "download_storage_file"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_files_download_endpoint,
            methods=["GET"],
            response_model=None,
            summary="Download storage file",
            description=None,
            tags=["Storage File"],
        )
