from typing import List
from app.api.domains.werkingsgebieden.endpoints.input_geo.input_geo_werkingsgebied_history_endpoint import (
    get_input_geo_werkingsgebieden_history_endpoint,
)
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebied
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class InputGeoWerkingsgebiedenHistoryEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "input_geo_werkingsgebieden_history"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=get_input_geo_werkingsgebieden_history_endpoint,
            methods=["GET"],
            response_model=List[InputGeoWerkingsgebied],
            summary="Get history of a input geo werkingsgebied by title",
            description=None,
            tags=["Input Geo"],
        )
