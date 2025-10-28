import uuid
from datetime import datetime, timezone
from typing import Annotated, Dict, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, File, HTTPException, UploadFile, status
from lxml import etree
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_announcement_package
from app.api.domains.publications.repository.publication_announcement_report_repository import (
    PublicationAnnouncementReportRepository,
)
from app.api.domains.publications.types.enums import PackageType, PublicationVersionStatus, ReportStatusType
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.permissions import Permissions
from app.api.utils.pagination import PaginatedQueryResult
from app.core.tables.publications import (
    PublicationAnnouncementPackageReportTable,
    PublicationAnnouncementPackageTable,
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
        announcement_package: PublicationAnnouncementPackageTable,
        created_by_uuid: uuid.UUID,
        timepoint: datetime,
    ):
        self._debug: bool = debug
        self._announcement_package: PublicationAnnouncementPackageTable = announcement_package
        self._created_by_uuid: uuid.UUID = created_by_uuid
        self._timepoint: datetime = timepoint
        self._namespaces: Dict[str, str] = {
            "lvbb": "http://www.overheid.nl/2017/lvbb",
            "stop": "http://www.overheid.nl/2017/stop",
        }

    def parse(self, file: UploadFile) -> PublicationAnnouncementPackageReportTable:
        content: bytes = file.file.read()
        file.file.close()

        report: PublicationAnnouncementPackageReportTable = self._parse_report_xml(content, file.filename or "")
        if not self._debug and report.Sub_Delivery_ID != self._announcement_package.Delivery_ID:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Report idLevering does not match publication package UUID")

        return report

    def _parse_report_xml(self, content: bytes, filename: str) -> PublicationAnnouncementPackageReportTable:
        """
        Parse the XML content to a dictionary of variables
        """
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

            report_table = PublicationAnnouncementPackageReportTable(
                UUID=uuid.uuid4(),
                Announcement_Package_UUID=self._announcement_package.UUID,
                Report_Status=report_status,
                Filename=filename,
                Source_Document=content.decode("utf-8"),
                Main_Outcome=main_outcome,
                Sub_Delivery_ID=sub_delivery_id,
                Sub_Progress=maybe_sub_progress or "",
                Sub_Outcome=maybe_sub_outcome or "",
                Created_Date=self._timepoint,
                Created_By_UUID=self._created_by_uuid,
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
        report_repository: PublicationAnnouncementReportRepository,
        user: UsersTable,
        uploaded_files: List[UploadFile],
        announcement_package: PublicationAnnouncementPackageTable,
    ):
        self._session: Session = session
        self._report_repository: PublicationAnnouncementReportRepository = report_repository
        self._user: UsersTable = user
        self._uploaded_files: List[UploadFile] = uploaded_files
        self._announcement_package: PublicationAnnouncementPackageTable = announcement_package
        self._timepoint: datetime = datetime.now(timezone.utc)
        self._starting_status: ReportStatusType = ReportStatusType(self._announcement_package.Report_Status)
        self._file_parser: FileParser = FileParser(
            debug=debug,
            announcement_package=announcement_package,
            created_by_uuid=user.UUID,
            timepoint=self._timepoint,
        )

    def handle(self) -> UploadPackageReportResponse:
        self._guard_can_upload_files()

        if not self._uploaded_files:
            raise HTTPException(status_code=400, detail="Missing uploaded files")

        duplicate_count: int = 0
        running_status: RunningStatus = RunningStatus(
            Status=ReportStatusType(self._announcement_package.Report_Status),
            Is_Conclusive=False,
        )
        for file in self._uploaded_files:
            existing_data: PaginatedQueryResult = self._report_repository.get_with_filters(
                self._session,
                announcement_package_uuid=self._announcement_package.UUID,
                filename=file.filename,
                limit=1,
            )
            if existing_data.total_count > 0:
                duplicate_count += 1
                continue

            report: PublicationAnnouncementPackageReportTable = self._file_parser.parse(file)
            self._session.add(report)
            running_status = self._update_running_status(running_status, report)

        self._handle_conclusive_status(running_status)

        self._announcement_package.Modified_By_UUID = self._user.UUID
        self._announcement_package.Modified_Date = self._timepoint

        self._session.add(self._announcement_package)
        self._session.flush()
        self._session.commit()

        response: UploadPackageReportResponse = UploadPackageReportResponse(
            Status=ReportStatusType(self._announcement_package.Report_Status),
            Duplicate_Count=duplicate_count,
        )
        return response

    def _guard_can_upload_files(self):
        if not self._announcement_package.Announcement.Publication.Environment.Has_State:
            raise HTTPException(status_code=400, detail="Can not upload packages for stateless environment")

    def _update_running_status(
        self,
        running_status: RunningStatus,
        report: PublicationAnnouncementPackageReportTable,
    ):
        if self._announcement_package.Report_Status == ReportStatusType.ABORTED:
            running_status.Status = ReportStatusType.ABORTED
            running_status.Is_Conclusive = True
            return running_status

        if self._announcement_package.Report_Status == ReportStatusType.FAILED:
            running_status.Status = ReportStatusType.FAILED
            running_status.Is_Conclusive = True
            return running_status

        if report.Report_Status == ReportStatusType.FAILED:
            running_status.Status = ReportStatusType.FAILED
            running_status.Is_Conclusive = True
            return running_status

        if report.Report_Status == ReportStatusType.VALID and report.Sub_Outcome:
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

        self._announcement_package.Report_Status = running_status.Status

        # If we did not create a new state (for example on validation)
        # Then we do not really have to do anything
        if self._announcement_package.Created_Environment_State_UUID is None:
            return

        match self._announcement_package.Report_Status:
            case ReportStatusType.FAILED:
                return self._handle_conclusive_failed()
            case ReportStatusType.VALID:
                return self._handle_conclusive_valid()

    def _handle_conclusive_failed(self):
        # On failed we just unlock the environment
        self._announcement_package.Announcement.Publication.Environment.Is_Locked = False
        self._session.add(self._announcement_package.Announcement.Publication.Environment)

    def _handle_conclusive_valid(self):
        environment: PublicationEnvironmentTable = self._announcement_package.Announcement.Publication.Environment
        new_state: PublicationEnvironmentStateTable = self._announcement_package.Created_Environment_State

        # On success we have to:
        # - Activate the new state
        # - Push the new state
        # - Unlock the environment
        # - Lock the Publication Version if the package was a Publication
        # - Complete the publication version Status
        new_state.Is_Activated = True
        new_state.Activated_Datetime = self._timepoint
        self._session.add(new_state)

        environment.Active_State_UUID = new_state.UUID
        environment.Is_Locked = False
        environment.Modified_Date = self._timepoint
        environment.Modified_By_UUID = self._user.UUID
        self._session.add(environment)

        if self._announcement_package.Package_Type == PackageType.PUBLICATION.value:
            self._announcement_package.Announcement.Is_Locked = True
            self._announcement_package.Announcement.Act_Package.Publication_Version.Status = (
                PublicationVersionStatus.COMPLETED
            )

            self._session.add(self._announcement_package.Announcement)


@inject
def post_upload_announcement_package_report_endpoint(
    announcement_package: Annotated[
        PublicationAnnouncementPackageTable, Depends(depends_publication_announcement_package)
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_upload_publication_announcement_package_report,
            )
        ),
    ],
    report_repository: Annotated[
        PublicationAnnouncementReportRepository,
        Depends(
            Provide[ApiContainer.publication.announcement_report_repository],
        ),
    ],
    session: Annotated[Session, Depends(depends_db_session)],
    debug: Annotated[bool, Depends(Provide[ApiContainer.config.DEBUG_MODE])],
    uploaded_files: Annotated[List[UploadFile], File(...)],
) -> UploadPackageReportResponse:
    handler = EndpointHandler(
        session=session,
        debug=debug,
        report_repository=report_repository,
        user=user,
        uploaded_files=uploaded_files,
        announcement_package=announcement_package,
    )
    return handler.handle()
