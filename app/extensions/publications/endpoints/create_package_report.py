import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.models import PublicationPackageReport
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.tables.tables import PublicationPackageReportTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class CreatePackageReportEndpoint(Endpoint):
    """
    Record the validation response of the submitted publication package
    and update the package status accordingly.
    """

    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        async def fastapi_handler(
            package_uuid: uuid.UUID,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            db: Session = Depends(depends_db),
            xml_file: UploadFile = File(...),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PublicationPackageReport:
            package = publication_repo.get_publication_package(uuid=package_uuid)
            if not package:
                raise HTTPException(status_code=404, detail="Package not found")

            # Parse XML report
            xml_content = await xml_file.read()
            report_db = self._parse_xml_to_publication_package_report(xml_content=xml_content)
            if report_db.Package_UUID != package_uuid:
                raise HTTPException(status_code=403, detail="Report idLevering does not match publication package UUID")

            report_db.Source_Document = xml_content.decode("utf-8")
            db.add(report_db)

            if report_db.Result != "succes":
                package.Validation_Status = "Invalid"
            else:
                # Check if all reports for this package are valid to mark the package as valid
                valid_reports_count = self._count_valid_reports(db, package_uuid)
                total_reports_count = self._count_total_reports(db, package_uuid)
                if valid_reports_count == total_reports_count:
                    package.Validation_Status = "Valid"
                # If there are no failed but not all reports are processed, it remains in Pending
            db.commit()

            report = PublicationPackageReport.from_orm(report_db)
            return report

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            summary=f"Record the submission response from lvbb of a publication package",
            response_model=PublicationPackageReport,
            description=None,
            tags=["Publications"],
        )

        return router

    def _count_valid_reports(self, db, package_uuid: uuid.UUID) -> int:
        """
        Count the number of valid reports for a package
        """
        return db.query(PublicationPackageReportTable).filter_by(Package_UUID=package_uuid, Result="succes").count()

    def _count_total_reports(self, db, package_uuid: uuid.UUID) -> int:
        """
        Count the total number of reports for a package
        """
        return db.query(PublicationPackageReportTable).filter_by(Package_UUID=package_uuid).count()

    def _parse_xml_to_publication_package_report(self, xml_content: str) -> PublicationPackageReportTable:
        """
        Parse the XML content to a PublicationPackageReportTable object
        """
        root = ET.fromstring(xml_content)
        namespace = {"lvbb": "http://www.overheid.nl/2017/lvbb", "stop": "http://www.overheid.nl/2017/stop"}
        uitkomst = root.find("lvbb:uitkomst", namespace).text
        verslag = root.find("lvbb:verslag", namespace)
        idLevering = uuid.UUID(verslag.find("lvbb:idLevering", namespace).text)  # Assuming idLevering is a valid UUID
        tijdstipVerslag = datetime.fromisoformat(
            verslag.find("lvbb:tijdstipVerslag", namespace).text.replace("Z", "+00:00")
        )
        meldingen = ET.tostring(verslag.find("lvbb:meldingen", namespace), encoding="unicode")
        voortgang = verslag.find("lvbb:voortgang", namespace).text

        return PublicationPackageReportTable(
            Created_Date=datetime.now(),
            Package_UUID=idLevering,
            Result=uitkomst,
            Report_Timestamp=tijdstipVerslag,
            Messages=meldingen,
            Report_Type=voortgang,
        )


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
