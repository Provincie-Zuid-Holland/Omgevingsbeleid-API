import uuid
from datetime import UTC, datetime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.publications.dependencies import depends_publication_version
from app.api.domains.publications.exceptions import DSOConfigurationException, DSORenvooiException
from app.api.domains.publications.services.act_package.act_package_builder import ActPackageBuilder
from app.api.domains.publications.services.act_package.act_package_builder_factory import ActPackageBuilderFactory
from app.api.domains.publications.services.publication_version_validator import PublicationVersionValidator
from app.api.domains.publications.services.validate_publication.validate_publication_service import (
    ValidatePublicationException,
)
from app.api.domains.publications.types.api_input_data import ActFrbr, BillFrbr, Purpose
from app.api.domains.publications.types.enums import (
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
        session: Session,
        validator: PublicationVersionValidator,
        package_builder_factory: ActPackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationPackageCreate,
        publication_version: PublicationVersionTable,
    ):
        self._session: Session = session
        self._validator: PublicationVersionValidator = validator
        self._package_builder_factory: ActPackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationPackageCreate = object_in
        self._publication_version: PublicationVersionTable = publication_version
        self._publication: PublicationTable = publication_version.publication
        self._environment: PublicationEnvironmentTable = publication_version.publication.environment
        self._act: PublicationActTable = publication_version.publication.act
        self._timepoint: datetime = datetime.now(UTC)

    def handle(self) -> PublicationPackageCreatedResponse:
        self._guard_validate_package_type()
        self._guard_locked()
        self._guard_valid_publication_version()

        try:
            package_builder: ActPackageBuilder = self._package_builder_factory.create_builder(
                self._session,
                self._publication_version,
                self._object_in.Package_Type,
            )
            package_builder.build_publication_files()
            zip_data: ZipData = package_builder.zip_files()

            report_status: ReportStatusType = ReportStatusType.NOT_APPLICABLE
            if self._environment.has_state:
                report_status = ReportStatusType.PENDING

            package_zip = PublicationPackageZipTable(
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

            package = PublicationActPackageTable(
                id=uuid.uuid4(),
                publication_version_id=self._publication_version.id,
                zip_id=package_zip.id,
                delivery_id=package_builder.get_delivery_id(),
                package_type=self._object_in.Package_Type,
                report_status=report_status,
                module_id=self._publication.module_id,
                module_status_id=self._publication_version.module_status_id,
                created_date=self._timepoint,
                modified_date=self._timepoint,
                created_by_id=self._user.UUID,
                modified_by_id=self._user.UUID,
            )
            self._session.add(package)
            self._session.flush()

            self._handle_new_state(package_builder, package)
            self._handle_bill_act_purpose(package_builder, package)

            if self._publication_version.status != PublicationVersionStatus.NOT_APPLICABLE:
                match self._object_in.Package_Type:
                    case PackageType.VALIDATION:
                        self._publication_version.status = PublicationVersionStatus.VALIDATION
                    case PackageType.PUBLICATION:
                        self._publication_version.status = PublicationVersionStatus.PUBLICATION
                self._session.add(self._publication_version)
                self._session.flush()

            self._session.commit()

            response = PublicationPackageCreatedResponse(
                Package_UUID=package.id,
                Zip_UUID=package_zip.id,
            )
            return response

        except HTTPException:
            # This is already correctly formatted
            raise
        except ValidationError as e:
            raise HTTPException(441, e.errors())
        except DSOConfigurationException as e:
            raise LoggedHttpException(status_code=442, detail=e.message) from e
        except DSORenvooiException as e:
            raise LoggedHttpException(status_code=443, detail=e.message, log_message=e.internal_error)
        except ValidatePublicationException as e:
            raise LoggedHttpException(status_code=444, detail=e.dump_errors(), log_message=e.dump_errors())
        except Exception:
            # We do not know what to except here
            # This will result in a 500 server error
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
        if self._publication_version.is_locked:
            raise HTTPException(status.HTTP_409_CONFLICT, "This publication version is locked")
        # allow creation of packages while validating, even when the environment is locked
        if self._environment.is_locked and self._object_in.Package_Type is not PackageType.VALIDATION:
            raise HTTPException(status.HTTP_409_CONFLICT, "This environment is locked")
        if not self._act.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT, "This act can no longer be used")

    def _guard_valid_publication_version(self):
        errors: list[ErrorDetails] = self._validator.get_errors(self._publication_version)
        if len(errors) != 0:
            raise HTTPException(status.HTTP_409_CONFLICT, errors)

    def _handle_new_state(self, package_builder: ActPackageBuilder, package: PublicationActPackageTable):
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

    def _handle_bill_act_purpose(self, package_builder: ActPackageBuilder, package: PublicationActPackageTable):
        if not self._environment.has_state:
            return
        if self._object_in.Package_Type != PackageType.PUBLICATION:
            return

        purpose: Purpose = package_builder.get_consolidation_purpose()
        purpose_table = PublicationPurposeTable(
            id=uuid.uuid4(),
            environment_id=self._environment.id,
            purpose_type=purpose.Purpose_Type,
            effective_date=purpose.Effective_Date,
            work_province_id=purpose.Work_Province_ID,
            work_date=purpose.Work_Date,
            work_other=purpose.Work_Other,
            created_date=self._timepoint,
            created_by_id=self._user.UUID,
        )
        self._session.add(purpose_table)
        self._session.flush()

        bill_frbr: BillFrbr = package_builder.get_bill_frbr()
        bill = PublicationBillTable(
            id=uuid.uuid4(),
            environment_id=self._environment.id,
            document_type=self._publication.document_type,
            work_province_id=bill_frbr.Work_Province_ID,
            work_country=bill_frbr.Work_Country,
            work_date=bill_frbr.Work_Date,
            work_other=bill_frbr.Work_Other,
            created_date=self._timepoint,
            modified_date=self._timepoint,
            created_by_id=self._user.UUID,
            modified_by_id=self._user.UUID,
        )
        self._session.add(bill)
        self._session.flush()

        bill_version = PublicationBillVersionTable(
            id=uuid.uuid4(),
            bill_id=bill.id,
            expression_language=bill_frbr.Expression_Language,
            expression_date=bill_frbr.Expression_Date,
            expression_version=bill_frbr.Expression_Version,
            created_date=self._timepoint,
            created_by_id=self._user.UUID,
        )
        self._session.add(bill_version)

        act_frbr: ActFrbr = package_builder.get_act_frbr()
        act_version = PublicationActVersionTable(
            id=uuid.uuid4(),
            act_id=self._act.uuid,
            consolidation_purpose_id=purpose_table.id,
            expression_language=act_frbr.Expression_Language,
            expression_date=act_frbr.Expression_Date,
            expression_version=act_frbr.Expression_Version,
            created_date=self._timepoint,
            created_by_id=self._user.UUID,
        )
        self._session.add(act_version)
        self._session.flush()

        package.bill_version_id = bill_version.id
        package.act_version_id = act_version.id
        self._session.add(package)
        self._session.flush()


@inject
def post_create_act_package_endpoint(
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
    session: Annotated[Session, Depends(depends_db_session)],
    object_in: PublicationPackageCreate,
) -> PublicationPackageCreatedResponse:
    handler: EndpointHandler = EndpointHandler(
        session,
        publication_version_validator,
        package_builder_factory,
        user,
        object_in,
        publication_version,
    )
    return handler.handle()
