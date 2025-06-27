
from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_template
from app.extensions.publications.models import PublicationTemplate
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationTemplateTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailPublicationTemplateEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            template: PublicationTemplateTable = Depends(depends_publication_template),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_template,
                )
            ),
        ) -> PublicationTemplate:
            result: PublicationTemplate = PublicationTemplate.model_validate(template)
            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationTemplate,
            summary=f"Get details of a publication template",
            description=None,
            tags=["Publication Templates"],
        )

        return router


class DetailPublicationTemplateEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_template"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{template_uuid}" in path:
            raise RuntimeError("Missing {template_uuid} argument in path")

        return DetailPublicationTemplateEndpoint(path)
