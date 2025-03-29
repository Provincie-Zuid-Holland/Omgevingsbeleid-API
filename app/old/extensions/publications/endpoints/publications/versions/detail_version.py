from typing import List

from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_version, depends_publication_version_validator
from app.extensions.publications.models import PublicationVersion
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.publication_version_validator import PublicationVersionValidator
from app.extensions.publications.tables.tables import PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class DetailPublicationVersionEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication_version: PublicationVersionTable = Depends(depends_publication_version),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_version,
                )
            ),
            validator: PublicationVersionValidator = Depends(depends_publication_version_validator),
        ) -> PublicationVersion:
            errors: List[dict] = validator.get_errors(publication_version)
            result: PublicationVersion = PublicationVersion.model_validate(publication_version)
            result.Errors = errors

            return result

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=PublicationVersion,
            summary=f"Get details of a publication version",
            description=None,
            tags=["Publication Versions"],
        )

        return router


class DetailPublicationVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication_version"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return DetailPublicationVersionEndpoint(path=path)
