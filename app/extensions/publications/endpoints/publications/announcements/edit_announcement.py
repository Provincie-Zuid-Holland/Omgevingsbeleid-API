from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_announcement
from app.extensions.publications.models.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationAnnouncementTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationAnnouncementEdit(BaseModel):
    Announcement_Date: Optional[date] = None

    Metadata: Optional[AnnouncementMetadata] = None
    Procedural: Optional[AnnouncementProcedural] = None
    Content: Optional[AnnouncementContent] = None


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        announcement: PublicationAnnouncementTable,
        object_in: PublicationAnnouncementEdit,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._announcement: PublicationAnnouncementTable = announcement
        self._object_in: PublicationAnnouncementEdit = object_in

    def handle(self) -> ResponseOK:
        self._guard_locked()

        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            if isinstance(value, BaseModel):
                value = value.dict()
            setattr(self._announcement, key, value)

        self._announcement.Modified_By_UUID = self._user.UUID
        self._announcement.Modified_Date = datetime.utcnow()

        self._db.add(self._announcement)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )

    def _guard_locked(self):
        if self._announcement.Is_Locked:
            raise HTTPException(status_code=409, detail="This announcement is locked")
        if not self._announcement.Publication.Act.Is_Active:
            raise HTTPException(status_code=409, detail="This act can no longer be used")


class EditPublicationAnnouncementEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationAnnouncementEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_announcement,
                ),
            ),
            announcement: PublicationAnnouncementTable = Depends(depends_publication_announcement),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                announcement,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary="Edit an existing publication announcement",
            description=None,
            tags=["Publication Announcements"],
        )

        return router


class EditPublicationAnnouncementEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_announcement"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{announcement_uuid}" in path:
            raise RuntimeError("Missing {announcement_uuid} argument in path")

        return EditPublicationAnnouncementEndpoint(path=path)
