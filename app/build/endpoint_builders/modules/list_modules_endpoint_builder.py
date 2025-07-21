from app.api.domains.modules.endpoints.list_modules_endpoint import (
    get_list_modules_endpoint,
)
from app.api.domains.modules.types import Module
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListModulesEndpointResolverBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_modules"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_modules_endpoint,
            methods=["GET"],
            response_model=PagedResponse[Module],
            summary="List the modules",
            description=None,
            tags=["Modules"],
        )
