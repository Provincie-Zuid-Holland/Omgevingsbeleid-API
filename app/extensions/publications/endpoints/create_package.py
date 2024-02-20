import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Optional

from dateutil.parser import parse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.core.settings import settings
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications import (
    DSOStateExportTable,
    MissingPublicationConfigError,
    PackageEventType,
    PublicationConfigTable,
    PublicationPackage,
    PublicationPackageTable,
)
from app.extensions.publications.dependencies import (
    depends_dso_service,
    depends_ow_object_repository,
    depends_publication_object_repository,
    depends_publication_repository,
)
from app.extensions.publications.dso.dso_service import DSOService
from app.extensions.publications.dso.ow_helpers import create_ow_objects_from_json
from app.extensions.publications.enums import DocumentType, ValidationStatusType
from app.extensions.publications.exceptions import PublicationBillNotFound
from app.extensions.publications.helpers import export_zip_to_filesystem
from app.extensions.publications.models import Publication, PublicationBill, PublicationConfig
from app.extensions.publications.repository import (
    OWObjectRepository,
    PublicationObjectRepository,
    PublicationRepository,
)
from app.extensions.publications.tables.ow import OWObjectTable
from app.extensions.publications.tables.tables import PublicationFRBRTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationPackageCreate(BaseModel):
    Config_ID: Optional[int]
    Announcement_Date: Optional[date]
    Package_Event_Type: PackageEventType

    @validator("Announcement_Date", pre=False, always=True)
    def validate_announcement_date(cls, v):
        if v is not None:
            effective_date = parse(v) if isinstance(v, str) else v
            if effective_date <= date.today():
                raise ValueError("Announcement Date must be in the future")
        return v


class CreatePublicationPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            bill_uuid: uuid.UUID,
            object_in: PublicationPackageCreate,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            pub_object_repo: PublicationObjectRepository = Depends(depends_publication_object_repository),
            ow_object_repo: OWObjectRepository = Depends(depends_ow_object_repository),
            db: Session = Depends(depends_db),
            dso_service: DSOService = Depends(depends_dso_service),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PublicationPackage:
            try:
                return self._handler(
                    user=user,
                    bill_uuid=bill_uuid,
                    object_in=object_in,
                    pub_repo=publication_repo,
                    dso_service=dso_service,
                    pub_object_repository=pub_object_repo,
                    ow_object_repo=ow_object_repo,
                    db=db,
                )
            except MissingPublicationConfigError:
                raise HTTPException(status_code=500, detail="No publication config found")
            except PublicationBillNotFound as e:
                raise HTTPException(status_code=404, detail=str(e))

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationPackage,
            summary="Create new Publication Package",
            tags=["Publications"],
        )

        return router

    def _get_config(self, pub_repo: PublicationRepository, config_id) -> PublicationConfig:
        # Defaults to latest config row
        if not config_id:
            current_config: PublicationConfigTable = pub_repo.get_latest_config()
        else:
            current_config: PublicationConfigTable = pub_repo.get_config_by_id(config_id=config_id)

        if not current_config:
            raise MissingPublicationConfigError("No config found")

        return PublicationConfig.from_orm(current_config)

    def _add_frbr_to_package(
        self,
        db: Session,
        document_type: DocumentType,
        bill_version_id: int,
        publication_work_id: int,
        new_package: PublicationPackageTable,
    ) -> PublicationPackage:
        frbr = None
        # If validation package, create new FRBR
        if new_package.Package_Event_Type == PackageEventType.VALIDATION:
            frbr = PublicationFRBRTable.create_default_frbr(
                document_type=document_type,
                expression_version=bill_version_id,
                work_ID=publication_work_id,
            )
            new_package.FRBR_Info = frbr
        else:
            # if publication event, try using earlier FRBR created at validation version of this bill
            stmt = (
                select(PublicationPackageTable)
                .where(
                    PublicationPackageTable.Bill_UUID == new_package.Bill_UUID,
                    PublicationPackageTable.Package_Event_Type == PackageEventType.VALIDATION,
                    PublicationPackageTable.Validation_Status == ValidationStatusType.VALID,
                )
                .order_by(desc(PublicationPackageTable.Modified_Date))
                .limit(1)
            )
            validated_package = db.execute(stmt).scalar()
            if not validated_package:
                raise ValueError("No validated package found for this bill")
            new_package.FRBR_ID = validated_package.FRBR_ID

        return new_package

    def _add_zip_to_package(self, new_package_db: PublicationPackageTable, zip_binary: bytes):
        """
        Add zip file to package and calculate filename + checksum
        """
        frbr = f"{new_package_db.FRBR_Info.bill_work_misc}-{new_package_db.FRBR_Info.bill_expression_version}"
        time = new_package_db.Created_Date.strftime("%Y-%m-%d_%H-%M")
        zip_filename = f"dso-{new_package_db.Package_Event_Type}-{frbr}-{time}.zip"
        new_package_db.ZIP_File_Name = zip_filename.lower()
        new_package_db.ZIP_File_Binary = zip_binary
        new_package_db.ZIP_File_Checksum = hashlib.sha256(zip_binary).hexdigest()

        return new_package_db

    def _handler(
        self,
        user: UsersTable,
        bill_uuid: uuid.UUID,
        pub_repo: PublicationRepository,
        object_in: PublicationPackageCreate,
        pub_object_repository: PublicationObjectRepository,
        ow_object_repo: OWObjectRepository,
        dso_service: DSOService,
        db: Session,
    ) -> PublicationPackage:
        """
        - Create new validation or publication package using this bill and config data
        - Call DSO Service build publication package files with external module
        - Save filtered export state in DB
        - Save new OW objects in DB
        - Return package UUID
        """
        current_config = self._get_config(pub_repo, object_in.Config_ID)

        bill_db = pub_repo.get_publication_bill(uuid=bill_uuid)
        if not bill_db:
            raise PublicationBillNotFound(f"Publication bill with UUID {bill_uuid} not found")

        bill = PublicationBill.from_orm(bill_db)
        publication = Publication.from_orm(bill_db.Publication)

        new_package_db = PublicationPackageTable(
            UUID=uuid.uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Created_By_UUID=user.UUID,
            Modified_By_UUID=user.UUID,
            Bill_UUID=bill.UUID,
            Config_ID=current_config.ID,
            Package_Event_Type=object_in.Package_Event_Type,
            Validation_Status=ValidationStatusType.PENDING.value,
            Announcement_Date=object_in.Announcement_Date if object_in.Announcement_Date else bill.Announcement_Date,
        )
        new_package_db = self._add_frbr_to_package(
            db=db,
            document_type=publication.Document_Type,
            publication_work_id=publication.Work_ID,
            bill_version_id=bill.Version_ID,
            new_package=new_package_db,
        )

        # TODO: move?
        try:
            template_parser = dso_service._template_parsers[publication.Document_Type]
        except KeyError:
            raise KeyError(f"No template parser found for document type {publication.Document_Type.value}")

        try:
            # Start a transaction
            db.add(new_package_db)

            # Create a savepoint right before the risky operation
            savepoint = db.begin_nested()
            package = PublicationPackage.from_orm(new_package_db)

            # Call DSO Service create package files
            objects = pub_object_repository.fetch_objects(
                module_id=bill_db.Publication.Module_ID,
                timepoint=datetime.utcnow(),
                object_types=template_parser.get_object_types(),
                field_map=template_parser.get_field_map(),
            )

            input_data = dso_service.prepare_publication_input(
                parser=template_parser,
                publication=publication,
                bill=bill,
                package=package,
                config=current_config,
                objects=objects,
                regelingsgebied=ow_object_repo.get_latest_regelinggebied(),
            )

            # Start DSO module
            try:
                dso_service.build_dso_package(input_data)
                savepoint.commit()
            except Exception as e:
                savepoint.rollback()
                raise e

            new_package_db = self._add_zip_to_package(
                new_package_db=new_package_db,
                zip_binary=dso_service._zip_buffer.getvalue(),
            )

            # Store zip result in temp folder for reference
            if settings.DSO_MODULE_DEBUG_EXPORT:
                try:
                    export_zip_to_filesystem(
                        zip_binary=new_package_db.ZIP_File_Binary,
                        zip_filename=new_package_db.ZIP_File_Name,
                        path=settings.DSO_MODULE_DEBUG_EXPORT_PATH,
                    )
                except Exception as e:
                    # notify but dont block
                    print("Failed to export zip to filesystem", e)

            # Save state and new objects in DB
            state_exported = json.loads(dso_service.get_filtered_export_state())
            db.add(
                DSOStateExportTable(
                    UUID=uuid.uuid4(),
                    Created_Date=datetime.now(),
                    Package_UUID=package.UUID,
                    Export_Data=state_exported,
                )
            )

            # Store new OW objects from DSO module in DB
            if new_package_db.Package_Event_Type == PackageEventType.PUBLICATION and bill_db.Is_Official:
                exported_ow_objects, exported_assoc_tables = create_ow_objects_from_json(
                    exported_state=state_exported,
                    bill_type=bill.Procedure_Type,
                )
                # generated OW ids by DSO module
                ow_ids = [ow_object.OW_ID for ow_object in exported_ow_objects]

                # Query for re-used OW objects
                stmt = select(OWObjectTable).where(OWObjectTable.OW_ID.in_(ow_ids))
                existing_ow_objects = db.execute(stmt).scalars().all()
                existing_ow_map = {ow_object.OW_ID: ow_object for ow_object in existing_ow_objects}

                for ow_object in list(exported_ow_objects):
                    if ow_object.OW_ID in existing_ow_map:
                        # OW obj already exists so just add this package as relation
                        existing_ow_map[ow_object.OW_ID].Packages.append(new_package_db)
                    else:
                        # new OW object
                        ow_object.Packages.append(new_package_db)
                        db.add(ow_object)

                # Add the OW assoc relations
                db.add_all(exported_assoc_tables)

                # Ensure any duplicate OW objects that were auto added by the ORM
                # are removed from the session.new state
                for obj in db.new:
                    if isinstance(obj, OWObjectTable):
                        if obj.OW_ID in existing_ow_map:
                            db.expunge(obj)

            db.commit()

            return PublicationPackage.from_orm(new_package_db)
        except Exception as e:
            db.rollback()
            raise e


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

        if not "{bill_uuid}" in path:
            raise RuntimeError("Missing {bill_uuid} argument in path")

        return CreatePublicationPackageEndpoint(path=path)
