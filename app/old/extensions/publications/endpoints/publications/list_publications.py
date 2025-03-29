from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.models import Publication
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository import PublicationRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationsEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            document_type: Optional[DocumentType] = None,
            module_id: Optional[int] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication,
                )
            ),
            publication_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PagedResponse[Publication]:
            return self._handler(
                publication_repository,
                document_type,
                module_id,
                pagination,
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

    def _handler(
        self,
        publication_repository: PublicationRepository,
        document_type: Optional[DocumentType],
        module_id: Optional[int],
        pagination: SimplePagination,
    ):
        paginated_result = publication_repository.get_with_filters(
            document_type=document_type,
            module_id=module_id,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [Publication.model_validate(r) for r in paginated_result.items]

        return PagedResponse[Publication](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publications"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationsEndpoint(path=path)
