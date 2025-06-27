from app.api.domains.publications.endpoints.acts.detail_act_endpoint import get_detail_act_endpoint
from app.api.domains.publications.types.models import PublicationAct
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailActEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_act"

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
            endpoint=get_detail_act_endpoint,
            methods=["GET"],
            response_model=PublicationAct,
            summary=f"Get details of a publication act",
            description=None,
            tags=["Publication Acts"],
        )
