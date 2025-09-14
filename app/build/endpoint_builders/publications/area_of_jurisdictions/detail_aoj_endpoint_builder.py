from app.api.domains.publications.endpoints.area_of_jurisdictions.detail_aoj_endpoint import get_detail_aoj_endpoint
from app.api.domains.publications.types.models import PublicationAOJ, PublicationAct
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class DetailPublicationAOJEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "detail_publication_area_of_jurisdictions"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_detail_aoj_endpoint,
            methods=["GET"],
            response_model=PublicationAOJ,
            summary="Get details of a publication area of jurisdictions",
            description=None,
            tags=["Publication AOJ"],
        )
