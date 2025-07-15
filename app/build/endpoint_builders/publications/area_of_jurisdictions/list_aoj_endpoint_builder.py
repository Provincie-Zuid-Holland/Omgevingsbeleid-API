from app.api.domains.publications.endpoints.area_of_jurisdictions.list_aoj_endpoint import get_list_aoj_endpoint
from app.api.domains.publications.types.models import PublicationAOJ
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationAOJEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_area_of_jurisdictions"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_list_aoj_endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationAOJ],
            summary="List the publication area of jurisdictions",
            description=None,
            tags=["Publication AOJ"],
        )
