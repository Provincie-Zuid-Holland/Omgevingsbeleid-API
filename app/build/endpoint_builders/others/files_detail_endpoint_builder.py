from app.api.domains.others.endpoints.files_detail_endpoint import get_files_detail_endpoint
from app.api.domains.others.types import StorageFileBasic
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailStorageFilesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_storage_file"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_files_detail_endpoint,
            methods=["GET"],
            response_model=StorageFileBasic,
            summary=f"Get storage file details",
            description=None,
            tags=["Storage File"],
        )
