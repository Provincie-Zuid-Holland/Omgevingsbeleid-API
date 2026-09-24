import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_announcement
from app.api.domains.publications.services.announcement_package.announcement_package_builder import (
    AnnouncementPackageBuilder,
)
from app.api.domains.publications.services.announcement_package.announcement_package_builder_factory import (
    AnnouncementPackageBuilderFactory,
)
from app.api.domains.publications.types.api_input_data import DocFrbr
from app.api.domains.publications.types.enums import PackageType, PublicationVersionStatus, ReportStatusType
from app.api.domains.publications.types.zip import ZipData
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.core.tables.publications import (
    PublicationAnnouncementPackageTable,
    PublicationAnnouncementTable,
    PublicationDocTable,
    PublicationDocVersionTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationPackageZipTable,
    PublicationTable,
)
from app.core.tables.users import UsersTable


class PublicationAnnouncementPackageCreate(BaseModel):
    Package_Type: PackageType


class PublicationAnnouncementPackageCreatedResponse(BaseModel):
    Package_UUID: uuid.UUID
    Zip_UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        package_builder_factory: AnnouncementPackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationAnnouncementPackageCreate,
        announcement: PublicationAnnouncementTable,
    ):
        self._session: Session = session
        self._package_builder_factory: AnnouncementPackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationAnnouncementPackageCreate = object_in
        self._announcement: PublicationAnnouncementTable = announcement
        self._publication: PublicationTable = announcement.publication
        self._environment: PublicationEnvironmentTable = announcement.publication.environment
        self._timepoint: datetime = datetime.now(UTC)

    def handle(self) -> PublicationAnnouncementPackageCreatedResponse:
        self._guard_validate_package_type()
        self._guard_locked()

        package_builder: AnnouncementPackageBuilder = self._package_builder_factory.create_builder(
            self._session,
            self._announcement,
            self._object_in.Package_Type,
        )
        try:
            package_builder.build_publication_files()
            zip_data: ZipData = package_builder.zip_files()

            report_status: ReportStatusType = ReportStatusType.NOT_APPLICABLE
            if self._environment.has_state:
                report_status = ReportStatusType.PENDING

            package_zip: PublicationPackageZipTable = PublicationPackageZipTable(
                id=uuid.uuid4(),
                filename=zip_data.Filename,
                binary=zip_data.Binary,
                checksum=zip_data.Checksum,
                latest_download_date=None,
                latest_download_by_uuid=None,
                created_date=self._timepoint,
                created_by_id=self._user.UUID,
            )
            self._session.add(package_zip)
            self._session.flush()

            package: PublicationAnnouncementPackageTable = PublicationAnnouncementPackageTable(
                id=uuid.uuid4(),
                announcement_id=self._announcement.id,
                zip_id=package_zip.id,
                delivery_id=package_builder.get_delivery_id(),
                package_type=self._object_in.Package_Type,
                report_status=report_status,
                created_date=self._timepoint,
                modified_date=self._timepoint,
                created_by_id=self._user.UUID,
                modified_by_id=self._user.UUID,
            )
            self._session.add(package)
            self._session.flush()

            self._handle_new_state(package_builder, package)
            self._handle_frbr(package_builder, package)

            # update publication version status to announcement
            self._announcement.act_package.publication_version.status = PublicationVersionStatus.ANNOUNCEMENT
            self._session.add(self._announcement.act_package.publication_version)

            self._session.commit()

            response: PublicationAnnouncementPackageCreatedResponse = PublicationAnnouncementPackageCreatedResponse(
                Package_UUID=package.id,
                Zip_UUID=package_zip.id,
            )
            return response

        except Exception:
            raise

    def _guard_validate_package_type(self):
        match self._object_in.Package_Type:
            case PackageType.VALIDATION:
                if not self._environment.can_validate:
                    raise HTTPException(status.HTTP_409_CONFLICT, "Can not create Validation for this environment")
            case PackageType.PUBLICATION:
                if not self._environment.can_publicate:
                    raise HTTPException(status.HTTP_409_CONFLICT, "Can not create Publication for this environment")

    def _guard_locked(self):
        if not self._publication.module.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT, "This module is not active")
        if self._announcement.is_locked:
            raise HTTPException(status.HTTP_409_CONFLICT, "This publication announcement is locked")
        if self._environment.is_locked:
            raise HTTPException(status.HTTP_409_CONFLICT, "This environment is locked")

    def _handle_new_state(
        self, package_builder: AnnouncementPackageBuilder, package: PublicationAnnouncementPackageTable
    ):
        if not self._environment.has_state:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        new_state: PublicationEnvironmentStateTable = package_builder.create_new_state()
        new_state.created_date = self._timepoint
        new_state.created_by_id = self._user.UUID
        self._session.add(new_state)
        self._session.flush()

        package.used_environment_state_id = self._environment.active_state_id
        package.created_environment_state_id = new_state.id
        self._session.add(package)
        self._session.flush()

        environment: PublicationEnvironmentTable = self._environment
        environment.is_locked = True
        self._session.add(environment)

    def _handle_frbr(self, package_builder: AnnouncementPackageBuilder, package: PublicationAnnouncementPackageTable):
        if not self._environment.has_state:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        doc_frbr: DocFrbr = package_builder.get_doc_frbr()
        doc: PublicationDocTable = PublicationDocTable(
            id=uuid.uuid4(),
            environment_id=self._environment.id,
            document_type=self._publication.document_type,
            work_province_id=doc_frbr.Work_Province_ID,
            work_country=doc_frbr.Work_Country,
            work_date=doc_frbr.Work_Date,
            work_other=doc_frbr.Work_Other,
            created_date=self._timepoint,
            modified_date=self._timepoint,
            created_by_id=self._user.UUID,
            modified_by_id=self._user.UUID,
        )
        self._session.add(doc)
        self._session.flush()

        doc_version = PublicationDocVersionTable(
            id=uuid.uuid4(),
            doc_id=doc.id,
            expression_language=doc_frbr.Expression_Language,
            expression_date=doc_frbr.Expression_Date,
            expression_version=doc_frbr.Expression_Version,
            created_date=self._timepoint,
            created_by_id=self._user.UUID,
        )
        self._session.add(doc_version)
        self._session.flush()

        # @todo: turn on
        # package.Doc_Version_UUID = doc_version.UUID
        self._session.add(package)
        self._session.flush()


@inject
def post_create_announcement_package_endpoint(
    announcement: Annotated[PublicationAnnouncementTable, Depends(depends_publication_announcement)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_announcement_package,
            )
        ),
    ],
    package_builder_factory: Annotated[
        AnnouncementPackageBuilderFactory,
        Depends(
            Provide[ApiContainer.publication.announcement_package_builder_factory],
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: PublicationAnnouncementPackageCreate,
) -> PublicationAnnouncementPackageCreatedResponse:
    handler: EndpointHandler = EndpointHandler(
        session,
        package_builder_factory,
        user,
        object_in,
        announcement,
    )
    return handler.handle()
