import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import depends_module_repository
from app.extensions.modules.repository.module_repository import ModuleRepository
from app.extensions.publications.dependencies import depends_publication_template_repository
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.extensions.publications.tables import PublicationTable
from app.extensions.publications.tables.tables import PublicationTable, PublicationTemplateTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationCreate(BaseModel):
    Module_ID: int
    Document_Type: DocumentType
    Template_UUID: uuid.UUID


class PublicationCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        module_repository: ModuleRepository,
        template_repository: PublicationTemplateRepository,
        user: UsersTable,
        object_in: PublicationCreate,
    ):
        self._db: Session = db
        self._module_repository: ModuleRepository = module_repository
        self._template_repository: PublicationTemplateRepository = template_repository
        self._user: UsersTable = user
        self._object_in: PublicationCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> PublicationCreatedResponse:
        module: ModuleTable = self._get_module()
        template: PublicationTemplateTable = self._get_template()

        publication: PublicationTable = PublicationTable(
            UUID=uuid.uuid4(),
            Module_ID=module.Module_ID,
            Document_Type=self._object_in.Document_Type,
            Template_UUID=template.UUID,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(publication)

        self._db.commit()
        self._db.flush()

        return PublicationCreatedResponse(
            UUID=publication.UUID,
        )

    def _get_module(self) -> ModuleTable:
        module: Optional[ModuleTable] = self._module_repository.get_by_id(
            self._object_in.Module_ID,
        )
        if module is None:
            raise HTTPException(status_code=404, detail="Module niet gevonden")
        if module.Closed:
            raise HTTPException(status_code=404, detail="Module is gesloten")

        return module

    def _get_template(self) -> PublicationTemplateTable:
        template: Optional[PublicationTemplateTable] = self._template_repository.get_by_uuid(
            self._object_in.Template_UUID,
        )
        if template is None:
            raise HTTPException(status_code=404, detail="Template niet gevonden")
        if not template.Is_Active:
            raise HTTPException(status_code=404, detail="Template is gesloten")

        return template


class CreatePublicationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(PublicationsPermissions.can_create_publication),
            ),
            module_repository: ModuleRepository = Depends(depends_module_repository),
            template_repository: PublicationTemplateRepository = Depends(depends_publication_template_repository),
            db: Session = Depends(depends_db),
        ) -> PublicationCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                module_repository,
                template_repository,
                user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationCreatedResponse,
            summary="Create a new publication",
            description=None,
            tags=["Publications"],
        )

        return router


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
