from app.api.domains.objects.endpoints.object_latest_endpoint import (
    ObjectLatestEndpointContext,
    view_object_latest_endpoint,
)
from app.api.domains.werkingsgebieden.endpoints.list_werkingsgebieden_endpoint import ListWerkingsgebiedenEndpointContext, get_list_werkingsgebieden_endpoint
from app.api.domains.werkingsgebieden.types import Werkingsgebied
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider
from app.core.types import Model



class ListWerkingsgebiedenEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "source_list_werkingsgebieden"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListWerkingsgebiedenEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_werkingsgebieden_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[Werkingsgebied],
            summary="List the werkingsgebieden",
            description=None,
            tags=["Source Werkingsgebieden"],
        )
