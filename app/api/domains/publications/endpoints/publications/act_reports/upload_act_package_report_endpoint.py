import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, HTTPException, UploadFile, status
from lxml import etree
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_act_package
from app.api.domains.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.api.domains.publications.types.enums import (
    PackageType,
    ProcedureType,
    PublicationVersionStatus,
    ReportStatusType,
)
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PaginatedQueryResult
from app.core.tables.publications import (
    PublicationActPackageReportTable,
    PublicationActPackageTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
)
from app.core.tables.users import UsersTable


class UploadPackageReportResponse(BaseModel):
    Status: ReportStatusType
    Duplicate_Count: int


class RunningStatus(BaseModel):
    Status: ReportStatusType
    Is_Conclusive: bool


class FileParser:
    def __init__(
        self,
        debug: bool,
        act_package: PublicationActPackageTable,
        created_by_id: uuid.UUID,
        timepoint: datetime,
    ):
        self._debug: bool = debug
        self._act_package: PublicationActPackageTable = act_package
        self._created_by_uuid: uuid.UUID = created_by_id
        self._timepoint: datetime = timepoint
        self._namespaces: dict[str, str] = {
            "lvbb": "http://www.overheid.nl/2017/lvbb",
            "stop": "http://www.overheid.nl/2017/stop",
        }

    def parse(self, file: UploadFile) -> PublicationActPackageReportTable:
        content: bytes = file.file.read()
        file.file.close()

        report: PublicationActPackageReportTable = self._parse_report_xml(content, file.filename or "")
        if not self._debug and report.sub_delivery_id != self._act_package.delivery_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Report idLevering does not match publication package UUID"
            )

        return report

    def _parse_report_xml(self, content: bytes, filename: str) -> PublicationActPackageReportTable:
        try:
            root = etree.fromstring(content, None)

            # We require these to exists, so we fetch them unsafely. If they do not exists, then the format is wrong and the file should fail
            main_outcome = root.xpath("//lvbb:uitkomst/text()", namespaces=self._namespaces)[0]
            sub_delivery_id = root.xpath("//lvbb:verslag/lvbb:idLevering/text()", namespaces=self._namespaces)[0]

            maybe_sub_progress: str = self._xml_get(root, "//lvbb:verslag/lvbb:voortgang/text()")
            maybe_sub_outcome: str = self._xml_get(root, "//lvbb:verslag/lvbb:uitkomst/text()")

            # This code is used by LVBB to indicate that the publication was a success
            is_published = root.xpath("//stop:code[text()='DL-0005']", namespaces=self._namespaces)
            if is_published:
                maybe_sub_outcome = maybe_sub_outcome or "Received code DL-0005"

            report_status = ReportStatusType.FAILED
            if main_outcome == "succes":
                report_status = ReportStatusType.VALID

            report_table = PublicationActPackageReportTable(
                id=uuid.uuid4(),
                act_package_id=self._act_package.id,
                report_status=report_status,
                filename=filename,
                source_document=content.decode("utf-8"),
                main_outcome=main_outcome,
                sub_delivery_id=sub_delivery_id,
                sub_progress=maybe_sub_progress or "",
                sub_outcome=maybe_sub_outcome or "",
                created_date=self._timepoint,
                created_by_id=self._created_by_uuid,
            )
            return report_table
        except Exception:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid file uploaded for filename: {filename}")

    def _xml_get(self, root, path: str, index: int = 0, default=""):
        matches = root.xpath(path, namespaces=self._namespaces)
        if index >= len(matches):
            return default
        return matches[index]


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        debug: bool,
        report_repository: PublicationActReportRepository,
        user: UsersTable,
        uploaded_files: list[UploadFile],
        act_package: PublicationActPackageTable,
    ):
        self._session: Session = session
        self._report_repository: PublicationActReportRepository = report_repository
        self._user: UsersTable = user
        self._uploaded_files: list[UploadFile] = uploaded_files
        self._act_package: PublicationActPackageTable = act_package
        self._timepoint: datetime = datetime.now(UTC)
        self._starting_status: ReportStatusType = ReportStatusType(self._act_package.report_status)
        self._file_parser: FileParser = FileParser(
            debug=debug,
            act_package=act_package,
            created_by_id=user.UUID,
            timepoint=self._timepoint,
        )

    def handle(self) -> UploadPackageReportResponse:
        self._guard_can_upload_files()

        if not self._uploaded_files:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing uploaded files")

        duplicate_count: int = 0
        running_status: RunningStatus = RunningStatus(
            Status=ReportStatusType(self._act_package.report_status),
            Is_Conclusive=False,
        )
        for file in self._uploaded_files:
            existing_data: PaginatedQueryResult = self._report_repository.get_with_filters(
                session=self._session,
                act_package_uuid=self._act_package.id,
                filename=file.filename,
                limit=1,
            )
            if existing_data.total_count > 0:
                duplicate_count += 1
                continue

            report: PublicationActPackageReportTable = self._file_parser.parse(file)
            self._session.add(report)
            running_status = self._update_running_status(running_status, report)

        self._handle_conclusive_status(running_status)

        self._act_package.modified_by_id = self._user.UUID
        self._act_package.modified_date = self._timepoint

        self._session.add(self._act_package)
        self._session.flush()
        self._session.commit()

        response: UploadPackageReportResponse = UploadPackageReportResponse(
            Status=ReportStatusType(self._act_package.report_status),
            Duplicate_Count=duplicate_count,
        )
        return response

    def _guard_can_upload_files(self):
        if not self._act_package.publication_version.publication.environment.has_state:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can not upload packages for stateless environment")

    def _update_running_status(
        self,
        running_status: RunningStatus,
        report: PublicationActPackageReportTable,
    ):
        if self._act_package.report_status == ReportStatusType.ABORTED:
            running_status.Status = ReportStatusType.ABORTED
            running_status.Is_Conclusive = True
            return running_status

        if self._act_package.report_status == ReportStatusType.FAILED:
            running_status.Status = ReportStatusType.FAILED
            running_status.Is_Conclusive = True
            return running_status

        if report.report_status == ReportStatusType.FAILED:
            running_status.Status = ReportStatusType.FAILED
            running_status.Is_Conclusive = True
            return running_status

        if report.report_status == ReportStatusType.VALID and report.sub_outcome:
            running_status.Status = ReportStatusType.VALID
            running_status.Is_Conclusive = True
            return running_status

        return running_status

    def _handle_conclusive_status(self, running_status: RunningStatus):
        """
        This will update the environment state and lock if needed
        """
        if running_status.Status == self._starting_status:
            # Nothing to do if nothing changed
            return

        # Nothing to do if not conclusive
        if not running_status.Is_Conclusive:
            return

        self._act_package.report_status = running_status.Status

        # If we did not create a new state (for example on validation)
        # Then we do not really have to do anything
        if self._act_package.created_environment_state_id is None:
            return

        match self._act_package.report_status:
            case ReportStatusType.FAILED:
                return self._handle_conclusive_failed()
            case ReportStatusType.VALID:
                return self._handle_conclusive_valid()

    def _handle_conclusive_failed(self):
        # On failed we just unlock the environment
        self._act_package.publication_version.publication.environment.is_locked = False
        self._session.add(self._act_package.publication_version.publication.environment)

        # Show failure in the publication version status
        match self._act_package.package_type:
            case PackageType.VALIDATION.value:
                self._act_package.publication_version.status = PublicationVersionStatus.VALIDATION_FAILED
            case PackageType.PUBLICATION.value:
                self._act_package.publication_version.status = PublicationVersionStatus.PUBLICATION_FAILED

        self._session.add(self._act_package.publication_version)

    def _handle_conclusive_valid(self):
        environment: PublicationEnvironmentTable = self._act_package.publication_version.publication.environment
        new_state: PublicationEnvironmentStateTable = self._act_package.created_environment_state

        # On success we have to:
        # - Activate the new state
        # - Push the new state
        # - Unlock the environment
        # - Lock the Publication Version if the package was a Publication
        # - Complete the publication version Status if the procedure type is final
        new_state.is_activated = True
        new_state.activated_datetime = self._timepoint
        self._session.add(new_state)

        environment.active_state_id = new_state.id
        environment.is_locked = False
        environment.modified_date = self._timepoint
        environment.modified_by_id = self._user.UUID
        self._session.add(environment)

        if self._act_package.package_type == PackageType.PUBLICATION.value:
            self._act_package.publication_version.is_locked = True

            if self._act_package.publication_version.publication.procedure_type == ProcedureType.FINAL.value:
                self._act_package.publication_version.status = PublicationVersionStatus.COMPLETED

            self._session.add(self._act_package.publication_version)


@inject
def post_upload_act_package_report_endpoint(
    act_package: Annotated[PublicationActPackageTable, Depends(depends_publication_act_package)],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_upload_publication_act_package_report,
            ),
        ),
    ],
    report_repository: Annotated[
        PublicationActReportRepository,
        Depends(
            Provide[ApiContainer.publication.act_report_repository],
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    debug: Annotated[bool, Depends(Provide[ApiContainer.config.DEBUG_MODE])],
    uploaded_files: Annotated[list[UploadFile], File(...)],
) -> UploadPackageReportResponse:
    handler: EndpointHandler = EndpointHandler(
        session,
        debug,
        report_repository,
        user,
        uploaded_files,
        act_package,
    )
    response: UploadPackageReportResponse = handler.handle()
    return response
