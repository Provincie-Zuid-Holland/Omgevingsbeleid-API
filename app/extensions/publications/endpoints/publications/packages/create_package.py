import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.core.settings import Settings
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_settings
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_package_builder_factory, depends_publication_version
from app.extensions.publications.enums import PackageType, ReportStatusType
from app.extensions.publications.models.api_input_data import Purpose
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.act_frbr_provider import ActFrbr
from app.extensions.publications.services.bill_frbr_provider import BillFrbr
from app.extensions.publications.services.package_builder import PackageBuilder, ZipData
from app.extensions.publications.services.package_builder_factory import PackageBuilderFactory
from app.extensions.publications.tables.tables import (
    PublicationActTable,
    PublicationActVersionTable,
    PublicationBillTable,
    PublicationBillVersionTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationPackageTable,
    PublicationPackageZipTable,
    PublicationPurposeTable,
    PublicationTable,
    PublicationVersionTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationPackageCreate(BaseModel):
    Package_Type: PackageType


class PublicationPackageCreatedResponse(BaseModel):
    Package_UUID: uuid.UUID
    Zip_UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        package_builder_factory: PackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationPackageCreate,
        publication_version: PublicationVersionTable,
    ):
        self._db: Session = db
        self._settings: Settings = settings
        self._package_builder_factory: PackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationPackageCreate = object_in
        self._publication_version: PublicationVersionTable = publication_version
        self._publication: PublicationTable = publication_version.Publication
        self._environment: PublicationEnvironmentTable = publication_version.Publication.Environment
        self._act: PublicationActTable = publication_version.Publication.Act
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> PublicationPackageCreatedResponse:
        self._guard_validate_package_type()
        self._guard_locked()

        package_builder: PackageBuilder = self._package_builder_factory.create_builder(
            self._publication_version,
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

            package: PublicationPackageTable = PublicationPackageTable(
                UUID=uuid.uuid4(),
                Publication_Version_UUID=self._publication_version.UUID,
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
            self._handle_bill_act_purpose(package_builder)

            self._db.commit()

            response: PublicationPackageCreatedResponse = PublicationPackageCreatedResponse(
                Package_UUID=package.UUID,
                Zip_UUID=package_zip.UUID,
            )
            return response

        except Exception as e:
            raise e

    def _guard_validate_package_type(self):
        match self._object_in.Package_Type:
            case PackageType.PUBLICATION_ABORT:
                raise NotImplementedError("Afbreek verzoek is nog niet geimplementeerd")
            case PackageType.VALIDATION:
                if not self._environment.Can_Validate:
                    raise HTTPException(status_code=409, detail="Can not create Validation for this environment")
            case PackageType.PUBLICATION:
                if not self._environment.Can_Publicate:
                    raise HTTPException(status_code=409, detail="Can not create Publication for this environment")

    def _guard_locked(self):
        if self._publication_version.Is_Locked:
            raise HTTPException(status_code=409, detail="This publication version is locked")
        if self._environment.Is_Locked:
            raise HTTPException(status_code=409, detail="This environment is locked")
        if not self._act.Is_Active:
            raise HTTPException(status_code=409, detail="This act can no longer be used")

    def _handle_new_state(self, package_builder: PackageBuilder, package: PublicationPackageTable):
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

    def _handle_bill_act_purpose(self, package_builder: PackageBuilder):
        if not self._environment.Has_State:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        purpose: Purpose = package_builder.get_consolidation_purpose()
        purpose_table: PublicationPurposeTable = PublicationPurposeTable(
            UUID=uuid.uuid4(),
            Environment_UUID=self._environment.UUID,
            Purpose_Type=purpose.Purpose_Type,
            Effective_Date=purpose.Effective_Date,
            Work_Province_ID=purpose.Work_Province_ID,
            Work_Date=purpose.Work_Date,
            Work_Other=purpose.Work_Other,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(purpose_table)
        self._db.flush()

        bill_frbr: BillFrbr = package_builder.get_bill_frbr()
        bill: PublicationBillTable = PublicationBillTable(
            UUID=uuid.uuid4(),
            Environment_UUID=self._environment.UUID,
            Document_Type=self._publication.Document_Type,
            Work_Province_ID=bill_frbr.Work_Province_ID,
            Work_Country=bill_frbr.Work_Country,
            Work_Date=bill_frbr.Work_Date,
            Work_Other=bill_frbr.Work_Other,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(bill)
        self._db.flush()
        bill_version: PublicationBillVersionTable = PublicationBillVersionTable(
            UUID=uuid.uuid4(),
            Bill_UUID=bill.UUID,
            Expression_Language=bill_frbr.Expression_Language,
            Expression_Date=bill_frbr.Expression_Date,
            Expression_Version=bill_frbr.Expression_Version,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(bill_version)

        act_frbr: ActFrbr = package_builder.get_act_frbr()
        act_version: PublicationActVersionTable = PublicationActVersionTable(
            UUID=uuid.uuid4(),
            Act_UUID=self._act.UUID,
            Consolidation_Purpose_UUID=purpose_table.UUID,
            Expression_Language=act_frbr.Expression_Language,
            Expression_Date=act_frbr.Expression_Date,
            Expression_Version=act_frbr.Expression_Version,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(act_version)


class CreatePublicationPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationPackageCreate,
            publication_version: PublicationVersionTable = Depends(depends_publication_version),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_package,
                )
            ),
            package_builder_factory: PackageBuilderFactory = Depends(depends_package_builder_factory),
            db: Session = Depends(depends_db),
            settings: Settings = Depends(depends_settings),
        ) -> PublicationPackageCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                settings,
                package_builder_factory,
                user,
                object_in,
                publication_version,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationPackageCreatedResponse,
            summary="Create new Publication Package",
            tags=["Publication Packages"],
        )

        return router


class CreatePublicationPackageEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_package"

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

        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return CreatePublicationPackageEndpoint(path=path)
