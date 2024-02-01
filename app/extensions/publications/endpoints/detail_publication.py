import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.models import Publication
from app.extensions.publications.repository import PublicationRepository


class DetailPublicationEndpoint(Endpoint):
    def __init__(self, event_dispatcher: EventDispatcher, path: str):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            # user: UsersTable = Depends(depends_current_active_user),
            publication_uuid: uuid.UUID,
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> Publication:
            publication = pub_repository.get_publication_by_uuid(publication_uuid)
            if not publication:
                raise HTTPException(status_code=404, detail=f"Publication: {publication_uuid} not found")

            return Publication.from_orm(publication)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=Publication,
            summary=f"Get details of a publication",
            description=None,
            tags=["Publications"],
        )

        return router


class DetailPublicationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "detail_publication"

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
        if not "{publication_uuid}" in path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return DetailPublicationEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
