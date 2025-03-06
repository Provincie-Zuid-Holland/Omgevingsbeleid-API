import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import (
    depends_publication_act_package,
    depends_publication_announcement_defaults_provider,
)
from app.extensions.publications.enums import ReportStatusType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.publication_announcement_defaults_provider import (
    PublicationAnnouncementDefaultsProvider,
)
from app.extensions.publications.tables.tables import (
    PublicationActPackageTable,
    PublicationActTable,
    PublicationAnnouncementTable,
    PublicationTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class AnnouncementCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        defaults_provider: PublicationAnnouncementDefaultsProvider,
        user: UsersTable,
        act_package: PublicationActPackageTable,
    ):
        self._db: Session = db
        self._defaults_provider: PublicationAnnouncementDefaultsProvider = defaults_provider
        self._user: UsersTable = user
        self._act_package: PublicationActPackageTable = act_package
        self._publication: PublicationTable = act_package.Publication_Version.Publication
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> AnnouncementCreatedResponse:
        self._guard_can_create_announcement()

        metadata = self._defaults_provider.get_metadata(
            self._publication.Document_Type, self._publication.Procedure_Type
        )
        procedural = self._defaults_provider.get_procedural()
        content = self._defaults_provider.get_content(self._publication.Document_Type, self._publication.Procedure_Type)

        announcement: PublicationAnnouncementTable = PublicationAnnouncementTable(
            UUID=uuid.uuid4(),
            Act_Package_UUID=self._act_package.UUID,
            Publication_UUID=self._publication.UUID,
            Metadata=metadata.model_dump(),
            Procedural=procedural.model_dump(),
            Content=content.model_dump(),
            Announcement_Date=None,
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(announcement)
        self._db.commit()
        self._db.flush()

        return AnnouncementCreatedResponse(
            UUID=announcement.UUID,
        )

    def _guard_can_create_announcement(self):
        if not self._publication.Environment.Has_State:
            return
        if self._act_package.Report_Status != ReportStatusType.VALID:
            raise HTTPException(
                status_code=409,
                detail="Can not create an announcement for act package that is not successful",
            )
        if not self._act_package.Act_Version.Act.Is_Active:
            raise HTTPException(
                status_code=409,
                detail="Can not create an announcement for act that is not active",
            )


class CreatePublicationAnnouncementEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            act_package: PublicationActTable = Depends(depends_publication_act_package),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_announcement,
                )
            ),
            defaults_provider: PublicationAnnouncementDefaultsProvider = Depends(
                depends_publication_announcement_defaults_provider
            ),
            db: Session = Depends(depends_db),
        ) -> AnnouncementCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                defaults_provider,
                user,
                act_package,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=AnnouncementCreatedResponse,
            summary="Create new publication announcement",
            description=None,
            tags=["Publication Announcements"],
        )

        return router


class CreatePublicationAnnouncementEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_announcement"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{act_package_uuid}" in path:
            raise RuntimeError("Missing {act_package_uuid} argument in path")

        return CreatePublicationAnnouncementEndpoint(path=path)
