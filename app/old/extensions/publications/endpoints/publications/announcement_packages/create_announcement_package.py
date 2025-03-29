import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import (
    depends_announcement_package_builder_factory,
    depends_publication_announcement,
)
from app.extensions.publications.enums import PackageType, PublicationVersionStatus, ReportStatusType
from app.extensions.publications.models.api_input_data import DocFrbr
from app.extensions.publications.models.zip import ZipData
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.announcement_package.announcement_package_builder import (
    AnnouncementPackageBuilder,
)
from app.extensions.publications.services.announcement_package.announcement_package_builder_factory import (
    AnnouncementPackageBuilderFactory,
)
from app.extensions.publications.tables.tables import (
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationDocTable,
    PublicationDocVersionTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationPackageZipTable,
    PublicationTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationAnnouncementPackageCreate(BaseModel):
    Package_Type: PackageType


class PublicationAnnouncementPackageCreatedResponse(BaseModel):
    Package_UUID: uuid.UUID
    Zip_UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        package_builder_factory: AnnouncementPackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationAnnouncementPackageCreate,
        announcement: PublicationAnnouncementTable,
    ):
        self._db: Session = db
        self._package_builder_factory: AnnouncementPackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationAnnouncementPackageCreate = object_in
        self._announcement: PublicationAnnouncementTable = announcement
        self._publication: PublicationTable = announcement.Publication
        self._environment: PublicationEnvironmentTable = announcement.Publication.Environment
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> PublicationAnnouncementPackageCreatedResponse:
        self._guard_validate_package_type()
        self._guard_locked()

        package_builder: AnnouncementPackageBuilder = self._package_builder_factory.create_builder(
            self._announcement,
            self._object_in.Package_Type,
        )
        try:
            package_builder.build_publication_files()
            zip_data: ZipData = package_builder.zip_files()

            report_status: ReportStatusType = ReportStatusType.NOT_APPLICABLE
            if self._environment.Has_State:
                report_status = ReportStatusType.PENDING

            package_zip: PublicationPackageZipTable = PublicationPackageZipTable(
                UUID=uuid.uuid4(),
                Filename=zip_data.Filename,
                Binary=zip_data.Binary,
                Checksum=zip_data.Checksum,
                Latest_Download_Date=None,
                Latest_Download_By_UUID=None,
                Created_Date=self._timepoint,
                Created_By_UUID=self._user.UUID,
            )
            self._db.add(package_zip)
            self._db.flush()

            package: PublicationAnnouncementPackageTable = PublicationAnnouncementPackageTable(
                UUID=uuid.uuid4(),
                Announcement_UUID=self._announcement.UUID,
                Zip_UUID=package_zip.UUID,
                Delivery_ID=package_builder.get_delivery_id(),
                Package_Type=self._object_in.Package_Type,
                Report_Status=report_status,
                Created_Date=self._timepoint,
                Modified_Date=self._timepoint,
                Created_By_UUID=self._user.UUID,
                Modified_By_UUID=self._user.UUID,
            )
            self._db.add(package)
            self._db.flush()

            self._handle_new_state(package_builder, package)
            self._handle_frbr(package_builder, package)

            # update publication version status to announcement
            self._announcement.Act_Package.Publication_Version.Status = PublicationVersionStatus.ANNOUNCEMENT
            self._db.add(self._announcement.Act_Package.Publication_Version)

            self._db.commit()

            response: PublicationAnnouncementPackageCreatedResponse = PublicationAnnouncementPackageCreatedResponse(
                Package_UUID=package.UUID,
                Zip_UUID=package_zip.UUID,
            )
            return response

        except Exception as e:
            raise e

    def _guard_validate_package_type(self):
        match self._object_in.Package_Type:
            case PackageType.VALIDATION:
                if not self._environment.Can_Validate:
                    raise HTTPException(status_code=409, detail="Can not create Validation for this environment")
            case PackageType.PUBLICATION:
                if not self._environment.Can_Publicate:
                    raise HTTPException(status_code=409, detail="Can not create Publication for this environment")

    def _guard_locked(self):
        if self._announcement.Is_Locked:
            raise HTTPException(status_code=409, detail="This publication announcement is locked")
        if self._environment.Is_Locked:
            raise HTTPException(status_code=409, detail="This environment is locked")

    def _handle_new_state(
        self, package_builder: AnnouncementPackageBuilder, package: PublicationAnnouncementPackageTable
    ):
        if not self._environment.Has_State:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        new_state: PublicationEnvironmentStateTable = package_builder.create_new_state()
        new_state.Created_Date = self._timepoint
        new_state.Created_By_UUID = self._user.UUID
        self._db.add(new_state)
        self._db.flush()

        package.Used_Environment_State_UUID = self._environment.Active_State_UUID
        package.Created_Environment_State_UUID = new_state.UUID
        self._db.add(package)
        self._db.flush()

        environment: PublicationEnvironmentTable = self._environment
        environment.Is_Locked = True
        self._db.add(environment)

    def _handle_frbr(self, package_builder: AnnouncementPackageBuilder, package: PublicationAnnouncementPackageTable):
        if not self._environment.Has_State:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        doc_frbr: DocFrbr = package_builder.get_doc_frbr()
        doc: PublicationDocTable = PublicationDocTable(
            UUID=uuid.uuid4(),
            Environment_UUID=self._environment.UUID,
            Document_Type=self._publication.Document_Type,
            Work_Province_ID=doc_frbr.Work_Province_ID,
            Work_Country=doc_frbr.Work_Country,
            Work_Date=doc_frbr.Work_Date,
            Work_Other=doc_frbr.Work_Other,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(doc)
        self._db.flush()

        doc_version: PublicationDocVersionTable = PublicationDocVersionTable(
            UUID=uuid.uuid4(),
            Doc_UUID=doc.UUID,
            Expression_Language=doc_frbr.Expression_Language,
            Expression_Date=doc_frbr.Expression_Date,
            Expression_Version=doc_frbr.Expression_Version,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(doc_version)
        self._db.flush()

        # @todo: turn on
        # package.Doc_Version_UUID = doc_version.UUID
        self._db.add(package)
        self._db.flush()


class CreatePublicationAnnouncementPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationAnnouncementPackageCreate,
            announcement: PublicationAnnouncementTable = Depends(depends_publication_announcement),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_announcement_package,
                )
            ),
            package_builder_factory: AnnouncementPackageBuilderFactory = Depends(
                depends_announcement_package_builder_factory
            ),
            db: Session = Depends(depends_db),
        ) -> PublicationAnnouncementPackageCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                package_builder_factory,
                user,
                object_in,
                announcement,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationAnnouncementPackageCreatedResponse,
            summary="Create new Publication Announcement Package",
            tags=["Publication Announcement Packages"],
        )

        return router


class CreatePublicationAnnouncementPackageEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_announcement_package"

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

        return CreatePublicationAnnouncementPackageEndpoint(path=path)
