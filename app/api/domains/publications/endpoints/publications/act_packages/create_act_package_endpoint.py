import uuid
from datetime import datetime, timezone
from typing import Annotated, List

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.exceptions import DSOConfigurationException, DSORenvooiException
from app.api.domains.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.api.domains.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.api.domains.publications.services.publication_version_validator import PublicationVersionValidator
from app.api.domains.publications.types.api_input_data import ActFrbr, BillFrbr, Purpose
from app.api.domains.publications.types.enums import (
    MutationStrategy,
    PackageType,
    PublicationVersionStatus,
    ReportStatusType,
)
from app.api.domains.publications.types.zip import ZipData
from app.api.domains.users.dependencies import depends_current_user_with_permission_curried
from app.api.exceptions import LoggedHttpException
from app.api.permissions import Permissions
from app.core.tables.publications import (
    PublicationActPackageTable,
    PublicationActTable,
    PublicationActVersionTable,
    PublicationBillTable,
    PublicationBillVersionTable,
    PublicationEnvironmentStateTable,
    PublicationEnvironmentTable,
    PublicationPackageZipTable,
    PublicationPurposeTable,
    PublicationTable,
    PublicationVersionTable,
)
from app.core.tables.users import UsersTable


class PublicationPackageCreate(BaseModel):
    Package_Type: PackageType


class PublicationPackageCreatedResponse(BaseModel):
    Package_UUID: uuid.UUID
    Zip_UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        validator: PublicationVersionValidator,
        package_builder_factory: ActPackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationPackageCreate,
        publication_version: PublicationVersionTable,
    ):
        self._db: Session = db
        self._validator: PublicationVersionValidator = validator
        self._package_builder_factory: ActPackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationPackageCreate = object_in
        self._publication_version: PublicationVersionTable = publication_version
        self._publication: PublicationTable = publication_version.Publication
        self._environment: PublicationEnvironmentTable = publication_version.Publication.Environment
        self._act: PublicationActTable = publication_version.Publication.Act
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> PublicationPackageCreatedResponse:
        self._guard_validate_package_type()
        self._guard_locked()
        self._guard_valid_publication_version()

        try:
            package_builder: ActPackageBuilder = self._package_builder_factory.create_builder(
                self._publication_version,
                self._object_in.Package_Type,
                MutationStrategy.RENVOOI,
            )
            package_builder.build_publication_files()
            zip_data: ZipData = package_builder.zip_files()

            report_status: ReportStatusType = ReportStatusType.NOT_APPLICABLE
            if self._environment.Has_State:
                report_status = ReportStatusType.PENDING

            package_zip = PublicationPackageZipTable(
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

            package = PublicationActPackageTable(
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
            self._handle_bill_act_purpose(package_builder, package)

            if self._publication_version.Status != PublicationVersionStatus.NOT_APPLICABLE:
                match self._object_in.Package_Type:
                    case PackageType.VALIDATION:
                        self._publication_version.Status = PublicationVersionStatus.VALIDATION
                    case PackageType.PUBLICATION:
                        self._publication_version.Status = PublicationVersionStatus.PUBLICATION
                self._db.add(self._publication_version)
                self._db.flush()

            self._db.commit()

            response = PublicationPackageCreatedResponse(
                Package_UUID=package.UUID,
                Zip_UUID=package_zip.UUID,
            )
            return response

        except HTTPException as e:
            # This is already correctly formatted
            raise e
        except ValidationError as e:
            raise HTTPException(441, e.errors())
        except DSOConfigurationException as e:
            raise LoggedHttpException(status_code=442, detail=e.message)
        except DSORenvooiException as e:
            raise LoggedHttpException(status_code=443, detail=e.message, log_message=e.internal_error)
        except Exception as e:
            # We do not know what to except here
            # This will result in a 500 server error
            raise e

    def _guard_validate_package_type(self):
        match self._object_in.Package_Type:
            case PackageType.VALIDATION:
                if not self._environment.Can_Validate:
                    raise HTTPException(status.HTTP_409_CONFLICT, "Can not create Validation for this environment")
            case PackageType.PUBLICATION:
                if not self._environment.Can_Publicate:
                    raise HTTPException(status.HTTP_409_CONFLICT, "Can not create Publication for this environment")

    def _guard_locked(self):
        if self._publication_version.Is_Locked:
            raise HTTPException(status.HTTP_409_CONFLICT, "This publication version is locked")
        if self._environment.Is_Locked:
            raise HTTPException(status.HTTP_409_CONFLICT, "This environment is locked")
        if not self._act.Is_Active:
            raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")

    def _guard_valid_publication_version(self):
        errors: List[dict] = self._validator.get_errors(self._publication_version)
        if len(errors) != 0:
            raise HTTPException(status.HTTP_409_CONFLICT, errors)

    def _handle_new_state(self, package_builder: ActPackageBuilder, package: PublicationActPackageTable):
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

    def _handle_bill_act_purpose(self, package_builder: ActPackageBuilder, package: PublicationActPackageTable):
        if not self._environment.Has_State:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        purpose: Purpose = package_builder.get_consolidation_purpose()
        purpose_table = PublicationPurposeTable(
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
        bill = PublicationBillTable(
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

        bill_version = PublicationBillVersionTable(
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
        act_version = PublicationActVersionTable(
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
        self._db.flush()

        package.Bill_Version_UUID = bill_version.UUID
        package.Act_Version_UUID = act_version.UUID
        self._db.add(package)
        self._db.flush()


@inject
async def post_create_act_package_endpoint(
    object_in: Annotated[PublicationPackageCreate, Depends()],
    publication_version: Annotated[PublicationVersionTable, Depends(depends_publication_version)],
    publication_version_validator: Annotated[
        PublicationVersionValidator, Depends(Provide[ApiContainer.publication.version_validator])
    ],
    user: Annotated[
        UsersTable,
        Depends(
            depends_current_user_with_permission_curried(
                Permissions.publication_can_create_publication_act_package,
            )
        ),
    ],
    package_builder_factory: Annotated[
        ActPackageBuilderFactory, Depends(Provide[ApiContainer.publication.act_package_builder_factory])
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
) -> PublicationPackageCreatedResponse:
    handler: EndpointHandler = EndpointHandler(
        db,
        publication_version_validator,
        package_builder_factory,
        user,
        object_in,
        publication_version,
    )
    return handler.handle()
