from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.domains.objects.endpoints.object_latest_endpoint import ObjectLatestEndpointContext, view_object_latest_endpoint
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder, EndpointConfig


class ObjectLatestEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "object_latest"

    def build_endpoint_config(
        self,
        # models_resolver: ModelsResolver,
        # endpoint_config: EndpointConfig,
        # api: Api,
    ) -> ConfiguiredFastapiEndpoint:
        data = {
            "response_type": AmbitieFull,
            "builder_data": {
                "endpoint_id": "object_latest",
                "path": "/ambitie/{lineage_id}/object-latest",
            }
        }
        # resolver_config: dict = endpoint_config.resolver_data
        # path: str = endpoint_config.prefix + resolver_config.get("path", "")
        
        context = ObjectLatestEndpointContext.model_validate(data)
        endpoint = self._inject_context(view_object_latest_endpoint, context=context)

        return ConfiguiredFastapiEndpoint(
            path="/ambitie/{lineage_id}/object-latest",
            endpoint=endpoint,
            methods=["GET"],
            response_class=JSONResponse,
            summary=f"View latest valid record for an Ambitie lineage id",
        )
