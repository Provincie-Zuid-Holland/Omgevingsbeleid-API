from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications import PublicationBill
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.enums import Document_Type
from app.extensions.publications.models import Publication
from app.extensions.publications.repository import PublicationRepository


class ListPublicationsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            # user: UsersTable = Depends(depends_current_active_user),
            document_type: Optional[Document_Type] = None,
            module_ID: Optional[int] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PagedResponse[PublicationBill]:
            paginated_result = pub_repository.list_publications(
                document_type=document_type,
                module_id=module_ID,
                limit=pagination.limit,
                offset=pagination.offset,
            )

            publications = [Publication.from_orm(r) for r in paginated_result.items]

            return PagedResponse[Publication](
                total=paginated_result.total_count,
                offset=pagination.offset,
                limit=pagination.limit,
                results=publications,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[Publication],
            summary="List the existing Publication",
            description=None,
            tags=["Publications"],
        )

        return router


class ListPublicationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publications"

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

        return ListPublicationsEndpoint(path=path)
