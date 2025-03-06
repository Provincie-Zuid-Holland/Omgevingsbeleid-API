from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_act_active
from app.extensions.publications.models.models import ActMetadata
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationActTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ActEdit(BaseModel):
    Title: Optional[str] = Field(None)
    Metadata: Optional[ActMetadata] = None


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        act: PublicationActTable,
        object_in: ActEdit,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._act: PublicationActTable = act
        self._object_in: ActEdit = object_in

    def handle(self) -> ResponseOK:
        changes: dict = self._object_in.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            if isinstance(value, BaseModel):
                value = value.model_dump()
            setattr(self._act, key, value)

        self._act.Modified_By_UUID = self._user.UUID
        self._act.Modified_Date = datetime.now(timezone.utc)

        self._db.add(self._act)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )


class EditPublicationActEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ActEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_act,
                ),
            ),
            act: PublicationActTable = Depends(depends_publication_act_active),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                act,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit publication act",
            description=None,
            tags=["Publication Acts"],
        )

        return router


class EditPublicationActEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_act"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{act_uuid}" in path:
            raise RuntimeError("Missing {act_uuid} argument in path")

        return EditPublicationActEndpoint(
            path=path,
        )
