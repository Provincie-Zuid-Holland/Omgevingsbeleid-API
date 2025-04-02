from typing import Optional

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_template_repository
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.models import PublicationTemplate
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ListPublicationTemplatesEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            is_active: Optional[bool] = None,
            document_type: Optional[DocumentType] = None,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_template,
                )
            ),
            template_repository: PublicationTemplateRepository = Depends(depends_publication_template_repository),
        ) -> PagedResponse[PublicationTemplate]:
            return self._handler(template_repository, is_active, document_type, pagination)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PagedResponse[PublicationTemplate],
            summary=f"List the publication templates",
            description=None,
            tags=["Publication Templates"],
        )

        return router

    def _handler(
        self,
        template_repository: PublicationTemplateRepository,
        is_active: Optional[bool],
        document_type: Optional[DocumentType],
        pagination: SimplePagination,
    ):
        paginated_result = template_repository.get_with_filters(
            is_active=is_active,
            document_type=document_type,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationTemplate.model_validate(r) for r in paginated_result.items]

        return PagedResponse[PublicationTemplate](
            total=paginated_result.total_count,
            offset=pagination.offset,
            limit=pagination.limit,
            results=results,
        )


class ListPublicationTemplatesEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_publication_templates"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationTemplatesEndpoint(path)
