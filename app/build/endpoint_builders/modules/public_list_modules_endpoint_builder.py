from app.api.domains.modules.endpoints.public_list_modules_endpoint import get_public_list_modules_endpoint
from app.api.domains.modules.types import PublicModuleShort
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class PublicListModulesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "public_list_modules"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_public_list_modules_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicModuleShort],
            summary=f"List the public modules",
            description=None,
            tags=["Public Modules"],
        )
