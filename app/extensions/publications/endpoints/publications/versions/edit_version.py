from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_version, depends_publication_version_validator
from app.extensions.publications.models import BillCompact, BillMetadata, Procedural
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.publication_version_validator import PublicationVersionValidator
from app.extensions.publications.tables.tables import PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationVersionEdit(BaseModel):
    Module_Status_ID: Optional[int]
    Effective_Date: Optional[date]
    Announcement_Date: Optional[date]

    Bill_Metadata: Optional[BillMetadata]
    Bill_Compact: Optional[BillCompact]
    Procedural: Optional[Procedural]


class PublicationVersionEditResponse(BaseModel):
    Errors: List[dict]
    Is_Valid: bool


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        validator: PublicationVersionValidator,
        user: UsersTable,
        version: PublicationVersionTable,
        object_in: PublicationVersionEdit,
    ):
        self._db: Session = db
        self._validator: PublicationVersionValidator = validator
        self._user: UsersTable = user
        self._version: PublicationVersionTable = version
        self._object_in: PublicationVersionEdit = object_in

    def handle(self) -> PublicationVersionEditResponse:
        self._guard_locked()

        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            if isinstance(value, BaseModel):
                value = value.dict()
            setattr(self._version, key, value)

        self._version.Modified_By_UUID = self._user.UUID
        self._version.Modified_Date = datetime.utcnow()

        self._db.add(self._version)
        self._db.commit()
        self._db.flush()

        errors: List[dict] = self._validator.get_errors(self._version)
        is_valid: bool = len(errors) == 0

        return PublicationVersionEditResponse(
            Errors=errors,
            Is_Valid=is_valid,
        )

    def _guard_locked(self):
        if not self._version.Publication.Act.Is_Active:
            raise HTTPException(status_code=409, detail="This act can no longer be used")


class EditPublicationVersionEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationVersionEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_version,
                ),
            ),
            version: PublicationVersionTable = Depends(depends_publication_version),
            validator: PublicationVersionValidator = Depends(depends_publication_version_validator),
            db: Session = Depends(depends_db),
        ) -> PublicationVersionEditResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                validator,
                user,
                version,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationVersionEditResponse,
            summary="Edit an existing publication version",
            description=None,
            tags=["Publication Versions"],
        )

        return router


class EditPublicationVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_version"

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

        return EditPublicationVersionEndpoint(path=path)
