from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.models import Publication
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.tables import PublicationTable
from app.extensions.publications.tables.tables import PublicationTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationCreate(BaseModel):
    Module_ID: int
    Document_Type: DocumentType
    Official_Title: str
    Regulation_Title: str
    Template_ID: Optional[int]


class CreatePublicationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationCreate,
            pub_repository: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> Publication:
            return self._handler(user=user, object_in=object_in, repo=pub_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=Publication,
            summary="Create a new publication",
            description=None,
            tags=["Publications"],
        )

        return router

    def _handler(self, user: UsersTable, object_in: PublicationCreate, repo: PublicationRepository):
        """
        Create a new publication if not existing for the given module and document type
        """
        # check if publication exists for module+document type
        existing = repo.list_publications(module_id=object_in.Module_ID, document_type=object_in.Document_Type)
        if existing.total_count != 0:
            raise ValueError(
                f"Publication UUID: {existing.items[0].UUID} already exists for this module and document type"
            )

        data = object_in.dict()
        new_publication = PublicationTable(
            UUID=uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Created_By_UUID=user.UUID,
            Modified_By_UUID=user.UUID,
            **data,
        )
        result = repo.create_publication(new_publication)
        return Publication.from_orm(result)


class CreatePublicationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication"

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
        return CreatePublicationEndpoint(path=path)
