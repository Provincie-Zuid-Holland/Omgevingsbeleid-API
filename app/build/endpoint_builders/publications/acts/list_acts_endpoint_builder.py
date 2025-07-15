from app.api.domains.publications.endpoints.acts.list_acts_endpoint import get_list_acts_endpoint
from app.api.domains.publications.types.models import PublicationActShort
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationActsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_acts"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_acts_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationActShort],
            summary="List the publication acts",
            description=None,
            tags=["Publication Acts"],
        )
