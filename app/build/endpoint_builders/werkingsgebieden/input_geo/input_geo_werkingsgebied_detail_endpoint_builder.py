from app.api.domains.werkingsgebieden.endpoints.input_geo.input_geo_werkingsgebied_detail_endpoint import (
    get_input_geo_werkingsgebieden_detail_endpoint,
)
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebiedDetailed
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class InputGeoWerkingsgebiedenDetailEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "input_geo_werkingsgebieden_detail"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_input_geo_werkingsgebieden_detail_endpoint,
            methods=["GET"],
            response_model=InputGeoWerkingsgebiedDetailed,
            summary="Get detailed response of a input geo werkingsgebied by its uuid",
            description=None,
            tags=["Input Geo"],
        )
