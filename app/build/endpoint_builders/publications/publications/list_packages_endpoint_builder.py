from app.api.domains.publications.endpoints.publications.packages.list_packages_endpoint import (
    ListPackagesEndpointContext,
    PublicationPackageListItem,
    get_list_packages_endpoint,
)
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPackagesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_packages"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListPackagesEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_packages_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackageListItem],
            summary="Generic overview of publication packages with filtering",
            description=None,
            tags=["Publication Packages"],
        )
