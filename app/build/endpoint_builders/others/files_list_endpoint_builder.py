from app.api.domains.others.endpoints.files_list_endpoint import get_files_list_endpoint
from app.api.domains.others.types import StorageFileBasic
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListStorageFilesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_storage_files"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_files_list_endpoint,
            methods=["GET"],
            response_model=PagedResponse[StorageFileBasic],
            summary="List the storage files",
            description=None,
            tags=["Storage File"],
        )
