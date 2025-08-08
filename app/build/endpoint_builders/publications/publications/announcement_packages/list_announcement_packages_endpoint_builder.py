from app.api.domains.publications.endpoints.publications.announcement_packages.list_announcement_packages_endpoint import (
    ListAnnouncementPackagesEndpointContext,
    get_list_announcement_packages_endpoint,
)
from app.api.domains.publications.types.models import PublicationPackage
from app.api.endpoint import EndpointContextBuilderData
from app.api.utils.pagination import OrderConfig, PagedResponse
from app.build.endpoint_builders.endpoint_builder import ConfiguredFastapiEndpoint, EndpointBuilder
from app.build.objects.types import EndpointConfig, ObjectApi
from app.core.services.models_provider import ModelsProvider


class ListPublicationAnnouncementPackagesEndpointBuilder(EndpointBuilder):
    def get_id(self) -> str:
        return "list_publication_announcement_packages"

    def build_endpoint(
        self,
        models_provider: ModelsProvider,
        builder_data: EndpointContextBuilderData,
        endpoint_config: EndpointConfig,
        api: ObjectApi,
    ) -> ConfiguredFastapiEndpoint:
        resolver_config: dict = endpoint_config.resolver_data
        order_config: OrderConfig = OrderConfig.from_dict(resolver_config["sort"])

        context = ListAnnouncementPackagesEndpointContext(
            order_config=order_config,
            builder_data=builder_data,
        )
        endpoint = self._inject_context(get_list_announcement_packages_endpoint, context)

        return ConfiguredFastapiEndpoint(
            path=builder_data.path,
            endpoint=endpoint,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackage],
            summary="List the existing publication announcement packages of a publication version",
            description=None,
            tags=["Publication Announcement Packages"],
        )
