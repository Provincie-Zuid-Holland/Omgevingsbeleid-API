from app.api.domains.publications.endpoints.acts.close_act_endpoint import post_close_act_endpoint
from app.api.endpoint import EndpointContextBuilderData
from app.api.types import ResponseOK
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ClosePublicationActEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "close_publication_act"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        if not "{act_uuid}" in builder_data.path:
            raise RuntimeError("Missing {act_uuid} argument in path")

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=post_close_act_endpoint,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Close publication act",
            description=None,
            tags=["Publication Acts"],
        )
