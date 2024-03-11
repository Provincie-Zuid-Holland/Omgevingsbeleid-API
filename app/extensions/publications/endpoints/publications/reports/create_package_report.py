import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from lxml import etree
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.core.settings import settings
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_package
from app.extensions.publications.enums import ValidationStatusType
from app.extensions.publications.models import PublicationPackageReport
from app.extensions.publications.tables.tables import PublicationPackageReportTable, PublicationPackageTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class CreatePackageReportResponse(BaseModel):
    Status: ValidationStatusType


class FileParser:
    def __init__(
        self,
        package_uuid: uuid.UUID,
        created_by_uuid: uuid.UUID,
        timepoint: datetime,
    ):
        self._package_uuid: uuid.UUID = package_uuid
        self._created_by_uuid: uuid.UUID = created_by_uuid
        self._timepoint: datetime = timepoint
        self._namespaces: Dict[str, str] = {
            "lvbb": "http://www.overheid.nl/2017/lvbb",
            "stop": "http://www.overheid.nl/2017/stop",
        }

    def parse(self, file: UploadFile) -> PublicationPackageReportTable:
        content = file.read()
        report_data = self._parse_report_xml(content, file.filename)
        if not settings.DEBUG_MODE and report_data.get("Package_UUID") != self._package_uuid:
            raise HTTPException(status_code=403, detail="Report idLevering does not match publication package UUID")

        report_db = PublicationPackageReportTable(
            Source_Document=content.decode("utf-8"),
            Filename=file.filename,
            **report_data,
        )
        report_db.Created_Date = self._timepoint
        report_db.Created_By_UUID = self._created_by_uuid
        report_db.Package_UUID = self._package_uuid

        return report_db

    def _parse_report_xml(self, content: str, filename: str) -> dict:
        """
        Parse the XML content to a dictionary of variables
        """
        try:
            root = etree.fromstring(content.encode("utf-8"))
            root_element_name = etree.QName(root).localname

            # We require these to exists, so we fetch them unsafely. If they do not exists, then the format is wrong and the file should fail
            outcome = root.xpath("//lvbb:uitkomst/text()", namespaces=self._namespaces)[0]
            package_uuid_str = root.xpath("//lvbb:verslag/lvbb:idLevering/text()", namespaces=self._namespaces)[0]
            report_timestamp = root.xpath("//lvbb:verslag/lvbb:tijdstipVerslag/text()", namespaces=self._namespaces)[0]

            maybe_report_progress = self._xml_get(root, "//lvbb:verslag/lvbb:voortgang/text()")
            maybe_report_outcome = self._xml_get(root, "//lvbb:uitkomst/text()", default=None)
            messages = self._xml_get_messages(root)

            result = ValidationStatusType.FAILED
            if outcome == "success":
                result = ValidationStatusType.VALID

            expected_final = False
            if result == ValidationStatusType.FAILED:
                expected_final = True
            if maybe_report_outcome is not None:
                expected_final = True

            return {
                "Package_UUID": uuid.UUID(package_uuid_str),
                "Outcome": outcome,
                "Result": result,
                "Expected_Final": expected_final,
                "Report_Timestamp": report_timestamp,
                "Messages": messages,
                "Report_Progress": maybe_report_progress,
            }
        except:
            return HTTPException(f"Invalid file uploaded for filename: {filename}")

    def _xml_get(self, root, path: str, index: int = 0, default=""):
        matches = root.xpath(path, namespaces=self._namespaces)
        if not index in matches:
            return default
        return matches[index]

    def _xml_get_messages(self, root) -> str:
        messages_elements = root.xpath("//lvbb:meldingen/lvbb:melding", namespaces=self._namespaces)
        messages = []
        for melding in messages_elements:
            code = melding.find("stop:code", self._namespaces).text
            ernst = melding.find("stop:ernst", self._namespaces).text
            soort = melding.find("stop:soort", self._namespaces).text
            beschrijving = melding.find("stop:beschrijving", self._namespaces).text
            messages.append(f"{code} {ernst} {soort} {beschrijving}")

        result = ", ".join(messages)
        return result


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        uploaded_files: List[UploadFile],
        package: PublicationPackageTable,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._uploaded_files: List[UploadFile] = uploaded_files
        self._package: PublicationPackageTable = package
        self._timepoint: datetime = datetime.utcnow()
        self._file_parser: FileParser = FileParser(
            package_uuid=package.UUID,
            created_by_uuid=user.UUID,
            timepoint=self._timepoint,
        )

    def handle(self) -> CreatePackageReportResponse:
        if not self._uploaded_files:
            raise HTTPException("Missing uploaded files")

        for file in self._uploaded_files:
            report: PublicationPackageReportTable = self._file_parser.parse(file)
            self._db.add(report)
            self._update_package_status(report)

        self._package.Modified_By_UUID = self._user.UUID
        self._package.Modified_Date = self._timepoint

        self._db.add(self._package)
        self._db.flush()

        response: CreatePackageReportResponse = CreatePackageReportResponse(
            Status=self._package.Validation_Status,
        )
        return response

    def _update_package_status(self, report: PublicationPackageReportTable):
        if self._package.Validation_Status == ValidationStatusType.FAILED:
            return

        if report.Result == ValidationStatusType.FAILED:
            self._package.Validation_Status = ValidationStatusType.FAILED
            return

        if report.Result == ValidationStatusType.VALID and report.Expected_Final:
            self._package.Validation_Status = ValidationStatusType.VALID
            return


class CreatePackageReportEndpoint(Endpoint):
    """
    Record the reports of the submitted publication package
    and update the package status accordingly.
    """

    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            package: PublicationPackageTable = Depends(depends_publication_package),
            uploaded_files: List[UploadFile] = File(...),
            user: UsersTable = Depends(depends_current_active_user),
            db: Session = Depends(depends_db),
        ) -> CreatePackageReportResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                uploaded_files,
                package,
            )
            response: CreatePackageReportResponse = handler.handle()
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Record the submission response from lvbb of a publication package",
            response_model=PublicationPackageReport,
            description=None,
            tags=["Publication Reports"],
        )

        return router


class CreatePackageReportEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_package_report"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{package_uuid}" in path:
            raise RuntimeError("Missing {package_uuid} argument in path")

        return CreatePackageReportEndpoint(path=path)
