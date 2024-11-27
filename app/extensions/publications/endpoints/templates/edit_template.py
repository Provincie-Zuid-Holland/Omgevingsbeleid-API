from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_template
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationTemplateTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class TemplateEdit(BaseModel):
    Title: Optional[str] = Field(None, nullable=True)
    Description: Optional[str] = Field(None, nullable=True)

    Is_Active: Optional[bool] = Field(None, nullable=True)
    Document_Type: Optional[DocumentType] = Field(None, nullable=True)
    Field_Map: Optional[List[str]] = Field(None, nullable=True)
    Object_Types: Optional[Dict[str, dict]] = Field(None, nullable=True)
    Text_Template: Optional[str] = Field(None, nullable=True)
    Object_Templates: Optional[Dict[str, str]] = Field(None, nullable=True)


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        template: PublicationTemplateTable,
        object_in: TemplateEdit,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._template: PublicationTemplateTable = template
        self._object_in: TemplateEdit = object_in

    def handle(self) -> ResponseOK:
        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            setattr(self._template, key, value)

        self._template.Modified_By_UUID = self._user.UUID
        self._template.Modified_Date = datetime.utcnow()

        self._db.add(self._template)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )


class EditPublicationTemplateEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: TemplateEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_template,
                ),
            ),
            template: PublicationTemplateTable = Depends(depends_publication_template),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                template,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit publication template",
            description=None,
            tags=["Publication Templates"],
        )

        return router


class EditPublicationTemplateEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_template"

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

        return EditPublicationTemplateEndpoint(
            path=path,
        )
