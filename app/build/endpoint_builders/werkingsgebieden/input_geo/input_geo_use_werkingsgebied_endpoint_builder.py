from app.api.domains.werkingsgebieden.endpoints.input_geo.input_geo_use_werkingsgebied_endpoint import (
    PatchResponse,
    PatchUseWerkingsgebiedContext,
    patch_input_geo_use_werkingsgebied_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class InputGeoUseWerkingsgebiedenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "input_geo_use_werkingsgebied"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        if "{module_id}" not in builder_data.path:
            raise RuntimeError("Missing {module_id} argument in path")
        if "{lineage_id}" not in builder_data.path:
            raise RuntimeError("Missing {lineage_id} argument in path")
        if "{input_geo_werkingsgebied_uuid}" not in builder_data.path:
            raise RuntimeError("Missing {input_geo_werkingsgebied_uuid} argument in path")

        resolver_config: dict = endpoint_config.resolver_data
        context = PatchUseWerkingsgebiedContext(
            builder_data=builder_data,
            object_type=api.object_type,
            target_object_type=resolver_config["target_object_type"],
        )
        endpoint = self._inject_context(patch_input_geo_use_werkingsgebied_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["PATCH"],
            response_model=PatchResponse,
            summary="Upgrade gebieden for {api.object_type} from input geo werkingsgebied",
            description=None,
            tags=[api.object_type],
        )
