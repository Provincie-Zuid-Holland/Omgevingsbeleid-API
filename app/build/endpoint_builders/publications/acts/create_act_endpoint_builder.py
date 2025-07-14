from app.api.domains.publications.endpoints.acts.create_act_endpoint import ActCreatedResponse, post_create_act_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class CreateActEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "create_publication_act"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_create_act_endpoint,
            methods=["POST"],
            response_model=ActCreatedResponse,
            summary="Create new Act",
            description=None,
            tags=["Publication Acts"],
        )
