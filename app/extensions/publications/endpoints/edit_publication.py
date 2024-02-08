import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.exceptions import PublicationNotFound
from app.extensions.publications.models import Publication
from app.extensions.publications.repository import PublicationRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationEdit(BaseModel):
    Template_ID: Optional[int]
    Official_Title: Optional[str]
    Regulation_Title: Optional[str]


class EditPublicationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication_uuid: uuid.UUID,
            object_in: PublicationEdit,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> Publication:
            return self._handler(
                user=user, publication_uuid=publication_uuid, object_in=object_in, repo=publication_repo
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PATCH"],
            response_model=Publication,
            summary="Edit an existing publication",
            description=None,
            tags=["Publications"],
        )

        return router

    def _handler(
        self, user: UsersTable, publication_uuid: uuid.UUID, repo: PublicationRepository, object_in: PublicationEdit
    ) -> Publication:
        # Only update provided fields that are not None
        data = object_in.dict()
        data = {k: v for k, v in data.items() if v is not None}
        data["Modified_By_UUID"] = user.UUID
        try:
            result = repo.update_publication(publication_uuid, **data)
        except PublicationNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))

        return Publication.from_orm(result)


class EditPublicationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication"

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
        return EditPublicationEndpoint(path=path)
