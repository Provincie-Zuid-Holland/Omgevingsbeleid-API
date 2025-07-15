from app.api.domains.publications.endpoints.environments.list_environments_endpoint import (
    get_list_environments_endpoint,
)
from app.api.domains.publications.types.models import PublicationEnvironment
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationEnvironmentsEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_environments"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_environments_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationEnvironment],
            summary="List the publication environments",
            description=None,
            tags=["Publication Environments"],
        )
