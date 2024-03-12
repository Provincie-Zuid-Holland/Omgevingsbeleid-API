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
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication, depends_publication_repository
from app.extensions.publications.models import Publication
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_template_repository import PublicationTemplateRepository
from app.extensions.publications.tables.tables import PublicationTable, PublicationTemplateTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationEdit(BaseModel):
    Template_UUID: Optional[uuid.UUID]
    Title: Optional[str]


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        template_repository: PublicationTemplateRepository,
        user: UsersTable,
        publication: PublicationTable,
        object_in: PublicationEdit,
    ):
        self._db: Session = db
        self._template_repository: PublicationTemplateRepository = template_repository
        self._user: UsersTable = user
        self._publication: PublicationTable = publication
        self._object_in: PublicationEdit = object_in

    def handle(self) -> ResponseOK:
        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        if self._object_in.Template_UUID is not None:
            _ = self._get_template(self._object_in.Template_UUID)

        for key, value in changes.items():
            setattr(self._publication, key, value)

        self._publication.Modified_By_UUID = self._user.UUID
        self._publication.Modified_Date = datetime.utcnow()

        self._db.add(self._publication)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )

    def _get_template(self, template_uuid: uuid.UUID) -> PublicationTemplateTable:
        template: Optional[PublicationTemplateTable] = self._template_repository.get_by_uuid(
            template_uuid,
        )
        if template is None:
            raise HTTPException(status_code=404, detail="Template niet gevonden")
        if template.Is_Active:
            raise HTTPException(status_code=404, detail="Template is gesloten")
        if template.Document_Type != self._object_in.Document_Type.value:
            raise HTTPException(status_code=404, detail="Template hoort niet bij dit document type")

        return template


class EditPublicationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication,
                ),
            ),
            publication: PublicationTable = Depends(depends_publication),
            template_repository: PublicationTemplateRepository = Depends(depends_publication_repository),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                template_repository,
                user,
                publication,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit an existing publication",
            description=None,
            tags=["Publications"],
        )

        return router


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
