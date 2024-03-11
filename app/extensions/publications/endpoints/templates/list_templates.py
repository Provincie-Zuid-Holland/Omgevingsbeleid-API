from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_simple_pagination
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PagedResponse, SimplePagination
from app.extensions.publications.dependencies import depends_publication_template_repository
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
            only_active: bool = True,
            pagination: SimplePagination = Depends(depends_simple_pagination),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_template,
                )
            ),
            template_repository: PublicationTemplateRepository = Depends(depends_publication_template_repository),
        ) -> PagedResponse[PublicationTemplate]:
            return self._handler(template_repository, only_active, pagination)

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
        only_active: bool,
        pagination: SimplePagination,
    ):
        paginated_result = template_repository.get_with_filters(
            only_active=only_active,
            offset=pagination.offset,
            limit=pagination.limit,
        )

        results = [PublicationTemplate.from_orm(r) for r in paginated_result.items]

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
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListPublicationTemplatesEndpoint(path)
