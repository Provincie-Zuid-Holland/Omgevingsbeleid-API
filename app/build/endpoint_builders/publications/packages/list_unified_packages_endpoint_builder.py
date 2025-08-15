from app.api.domains.publications.endpoints.publications.packages.list_unified_packages_endpoint import (
    get_list_unified_packages_endpoint,
    ListUnifiedPackagesEndpointContext,
    UnifiedPackage,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListUnifiedPackagesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_unified_publication_packages"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListUnifiedPackagesEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_unified_packages_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[UnifiedPackage],
            summary="List all publication packages (act and announcement)",
            tags=["Publication Packages"],
        )
