import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from lxml import etree
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db, depends_settings
from app.core.settings.dynamic_settings import DynamicSettings
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.pagination import PaginatedQueryResult
from app.extensions.publications.dependencies import (
    depends_publication_act_package,
    depends_publication_act_report_repository,
)
from app.extensions.publications.enums import PackageType, ProcedureType, ReportStatusType, PublicationVersionStatus
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_act_report_repository import PublicationActReportRepository
from app.extensions.publications.tables.tables import (
    PublicationActPackageReportTable,
    PublicationActPackageTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class UploadPackageReportResponse(BaseModel):
    Status: ReportStatusType
    Duplicate_Count: int


class RunningStatus(BaseModel):
    Status: ReportStatusType
    Is_Conclusive: bool


class FileParser:
    def __init__(
        self,
        settings: DynamicSettings,
        act_package: PublicationActPackageTable,
        created_by_uuid: uuid.UUID,
        timepoint: datetime,
    ):
        self._settings: DynamicSettings = settings
        self._act_package: PublicationActPackageTable = act_package
        self._created_by_uuid: uuid.UUID = created_by_uuid
        self._timepoint: datetime = timepoint
        self._namespaces: Dict[str, str] = {
            "lvbb": "http://www.overheid.nl/2017/lvbb",
            "stop": "http://www.overheid.nl/2017/stop",
        }

    def parse(self, file: UploadFile) -> PublicationActPackageReportTable:
        content: bytes = file.file.read()
        file.file.close()

        report: PublicationActPackageReportTable = self._parse_report_xml(content, file.filename)
        if not self._settings.DEBUG_MODE and report.Sub_Delivery_ID != self._act_package.Delivery_ID:
            raise HTTPException(status_code=403, detail="Report idLevering does not match publication package UUID")

        return report

    def _parse_report_xml(self, content: bytes, filename: str) -> PublicationActPackageReportTable:
        """
        Parse the XML content to a dictionary of variables
        """
        try:
            root = etree.fromstring(content)
            root_element_name = etree.QName(root).localname

            # We require these to exists, so we fetch them unsafely. If they do not exists, then the format is wrong and the file should fail
            main_outcome = root.xpath("//lvbb:uitkomst/text()", namespaces=self._namespaces)[0]
            sub_delivery_id = root.xpath("//lvbb:verslag/lvbb:idLevering/text()", namespaces=self._namespaces)[0]

            maybe_sub_progress: str = self._xml_get(root, "//lvbb:verslag/lvbb:voortgang/text()")
            maybe_sub_outcome: str = self._xml_get(root, "//lvbb:verslag/lvbb:uitkomst/text()")

            report_status = ReportStatusType.FAILED
            if main_outcome == "succes":
                report_status = ReportStatusType.VALID

            report_table = PublicationActPackageReportTable(
                UUID=uuid.uuid4(),
                Act_Package_UUID=self._act_package.UUID,
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
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid file uploaded for filename: {filename}")

    def _xml_get(self, root, path: str, index: int = 0, default=""):
        matches = root.xpath(path, namespaces=self._namespaces)
        if index >= len(matches):
            return default
        return matches[index]


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        settings: DynamicSettings,
        report_repository: PublicationActReportRepository,
        user: UsersTable,
        uploaded_files: List[UploadFile],
        act_package: PublicationActPackageTable,
    ):
        self._db: Session = db
        self._report_repository: PublicationActReportRepository = report_repository
        self._user: UsersTable = user
        self._uploaded_files: List[UploadFile] = uploaded_files
        self._act_package: PublicationActPackageTable = act_package
        self._timepoint: datetime = datetime.utcnow()
        self._starting_status: ReportStatusType = self._act_package.Report_Status
        self._file_parser: FileParser = FileParser(
            settings=settings,
            act_package=act_package,
            created_by_uuid=user.UUID,
            timepoint=self._timepoint,
        )

    def handle(self) -> UploadPackageReportResponse:
        self._guard_can_upload_files()

        if not self._uploaded_files:
            raise HTTPException(status_code=400, detail="Missing uploaded files")

        duplicate_count: int = 0
        running_status: RunningStatus = RunningStatus(
            Status=self._act_package.Report_Status,
            Is_Conclusive=False,
        )
        for file in self._uploaded_files:
            existing_data: PaginatedQueryResult = self._report_repository.get_with_filters(
                act_package_uuid=self._act_package.UUID,
                filename=file.filename,
                limit=1,
            )
            if existing_data.total_count > 0:
                duplicate_count += 1
                continue

            report: PublicationActPackageReportTable = self._file_parser.parse(file)
            self._db.add(report)
            running_status = self._update_running_status(running_status, report)

        self._handle_conclusive_status(running_status)

        self._act_package.Modified_By_UUID = self._user.UUID
        self._act_package.Modified_Date = self._timepoint

        self._db.add(self._act_package)
        self._db.flush()
        self._db.commit()

        response: UploadPackageReportResponse = UploadPackageReportResponse(
            Status=self._act_package.Report_Status,
            Duplicate_Count=duplicate_count,
        )
        return response

    def _guard_can_upload_files(self):
        if not self._act_package.Publication_Version.Publication.Environment.Has_State:
            raise HTTPException(status_code=400, detail="Can not upload packages for stateless environment")

    def _update_running_status(
        self,
        running_status: RunningStatus,
        report: PublicationActPackageReportTable,
    ):
        if self._act_package.Report_Status == ReportStatusType.FAILED:
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

        self._act_package.Report_Status = running_status.Status

        # If we did not create a new state (for example on validation)
        # Then we do not really have to do anything
        if self._act_package.Created_Environment_State_UUID is None:
            return

        match self._act_package.Report_Status:
            case ReportStatusType.FAILED:
                return self._handle_conclusive_failed()
            case ReportStatusType.VALID:
                return self._handle_conclusive_valid()

    def _handle_conclusive_failed(self):
        # On failed we just unlock the environment
        self._act_package.Publication_Version.Publication.Environment.Is_Locked = False
        self._db.add(self._act_package.Publication_Version.Publication.Environment)

        # Show failure in the publication version status
        match self._act_package.Package_Type:
            case PackageType.VALIDATION.value:
                self._act_package.Publication_Version.Status = PublicationVersionStatus.VALIDATION_FAILED
            case PackageType.PUBLICATION.value:
                self._act_package.Publication_Version.Status = PublicationVersionStatus.PUBLICATION_FAILED

        self._db.add(self._act_package.Publication_Version)

    def _handle_conclusive_valid(self):
        environment: PublicationEnvironmentTable = self._act_package.Publication_Version.Publication.Environment
        new_state: PublicationEnvironmentStateTable = self._act_package.Created_Environment_State

        # On success we have to:
        # - Activate the new state
        # - Push the new state
        # - Unlock the environment
        # - Lock the Publication Version if the package was a Publication
        # - Complete the publication version Status if the procedure type is final
        new_state.Is_Activated = True
        new_state.Activated_Datetime = self._timepoint
        self._db.add(new_state)

        environment.Active_State_UUID = new_state.UUID
        environment.Is_Locked = False
        environment.Modified_Date = self._timepoint
        environment.Modified_By_UUID = self._user.UUID
        self._db.add(environment)

        if self._act_package.Package_Type == PackageType.PUBLICATION.value:
            self._act_package.Publication_Version.Is_Locked = True

            if self._act_package.Publication_Version.Publication.Procedure_Type == ProcedureType.FINAL.value:
                self._act_package.Publication_Version.Status = PublicationVersionStatus.COMPLETED

            self._db.add(self._act_package.Publication_Version)


class UploadActPackageReportEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            act_package: PublicationActPackageTable = Depends(depends_publication_act_package),
            uploaded_files: List[UploadFile] = File(...),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_upload_publication_act_package_report,
                )
            ),
            report_repository: PublicationActReportRepository = Depends(depends_publication_act_report_repository),
            db: Session = Depends(depends_db),
            settings: DynamicSettings = Depends(depends_settings),
        ) -> UploadPackageReportResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                settings,
                report_repository,
                user,
                uploaded_files,
                act_package,
            )
            response: UploadPackageReportResponse = handler.handle()
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Record the submission response from lvbb of a publication package",
            response_model=UploadPackageReportResponse,
            description=None,
            tags=["Publication Act Reports"],
        )

        return router


class UploadActPackageReportEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "upload_publication_act_package_report"

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

        return UploadActPackageReportEndpoint(path=path)
