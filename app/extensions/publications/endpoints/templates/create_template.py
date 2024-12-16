import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables import PublicationTemplateTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class TemplateCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str
    Document_Type: DocumentType
    Object_Types: Dict[str, dict]
    Field_Map: List[str]
    Text_Template: str
    Object_Templates: Dict[str, str]


class TemplateCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_in: TemplateCreate,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_in: TemplateCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> TemplateCreatedResponse:
        template: PublicationTemplateTable = PublicationTemplateTable(
            UUID=uuid.uuid4(),
            Title=self._object_in.Title,
            Description=self._object_in.Description,
            Is_Active=True,
            Document_Type=self._object_in.Document_Type,
            Object_Types=self._object_in.Object_Types,
            Field_Map=self._object_in.Field_Map,
            Text_Template=self._object_in.Text_Template,
            Object_Templates=self._object_in.Object_Templates,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(template)

        self._db.flush()
        self._db.commit()

        return TemplateCreatedResponse(
            UUID=template.UUID,
        )


class CreatePublicationTemplateEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: TemplateCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_template,
                ),
            ),
            db: Session = Depends(depends_db),
        ) -> TemplateCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=TemplateCreatedResponse,
            summary=f"Create new publication template",
            description=None,
            tags=["Publication Templates"],
        )

        return router


class CreatePublicationTemplateEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_template"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return CreatePublicationTemplateEndpoint(path=path)
