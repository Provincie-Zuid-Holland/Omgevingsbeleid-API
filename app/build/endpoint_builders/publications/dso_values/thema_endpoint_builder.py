from app.api.domains.publications.endpoints.dso_value_lists import get_thema_endpoint
from app.api.domains.publications.endpoints.dso_value_lists.thema_endpoint import ListThemaResponse
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services import ModelsProvider


class ListThemaEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_thema"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_thema_endpoint,
            methods=["GET"],
            response_model=ListThemaResponse,
            summary="List the available themas to use for this publication",
            description=None,
            tags=["Publication Value Lists"],
        )
