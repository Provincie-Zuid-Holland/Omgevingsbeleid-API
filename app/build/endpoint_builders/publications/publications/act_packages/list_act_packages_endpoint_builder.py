from app.api.domains.publications.endpoints.publications.act_packages.list_act_packages_endpoint import (
    ListActPackagesEndpointContext,
    get_list_act_packages_endpoint,
)
from app.api.domains.publications.types.models import PublicationPackage
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguiredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationPackagesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_act_packages"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguiredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListActPackagesEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_act_packages_endpoint, context)

        return ConfiguiredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackage],
            summary="List the existing publication act packages of a publication version",
            description=None,
            tags=["Publication Act Packages"],
        )
