import uuid
from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications import PublicationPackage
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.enums import Package_Event_Type
from app.extensions.publications.repository.publication_repository import PublicationRepository


class ListPublicationPackagesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            bill_uuid: uuid.UUID,
            package_event_type: Optional[Package_Event_Type] = None,
            is_successful: Optional[bool] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            publication_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PagedResponse[PublicationPackage]:
            paginated_result = publication_repository.get_publication_packages(
                bill_uuid=bill_uuid, package_event_type=package_event_type, is_successful=is_successful
            )

            packages = [PublicationPackage.from_orm(r) for r in paginated_result.items]

            return PagedResponse[PublicationPackage](
                total=paginated_result.total_count,
                offset=pagination.offset,
                limit=pagination.limit,
                results=packages,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationPackage],
            summary="List the existing publication Packages",
            description=None,
            tags=["Publications"],
        )

        return router


class ListPublicationPackagesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_packages"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationPackagesEndpoint(
            path=path,
        )
