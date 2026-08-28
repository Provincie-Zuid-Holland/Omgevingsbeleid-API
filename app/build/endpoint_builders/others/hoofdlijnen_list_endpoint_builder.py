from app.api.domains.others.endpoints.hoofdlijnen_list_endpoint import get_hoofdlijnen_list_endpoint
from app.api.domains.others.types import Hoofdlijn
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListHoofdlijnenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_hoofdlijnen"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_hoofdlijnen_list_endpoint,
            methods=["GET"],
            response_model=PagedResponse[Hoofdlijn],
            summary="List hoofdlijnen",
            description=None,
            tags=["Hoofdlijn"],
        )
