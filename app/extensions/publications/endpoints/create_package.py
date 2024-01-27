import json
import uuid
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications import (
    MissingPublicationConfigError,
    Package_Event_Type,
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
from app.extensions.publications.dso.ow_export import create_ow_objects_from_json
from app.extensions.publications.exceptions import PublicationBillNotFound
from app.extensions.publications.models import PublicationBill, PublicationConfig
from app.extensions.publications.repository.ow_object_repository import OWObjectRepository
from app.extensions.publications.repository.publication_object_repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_repository import PublicationRepository
from app.extensions.publications.tables import PublicationConfigTable
from app.extensions.publications.tables.tables import DSOStateExportTable


class PublicationPackageCreate(BaseModel):
    """
    Represents a publication package creation request.

    Attributes:
        Bill_UUID (uuid.UUID): The UUID of the bill associated with the package.
        Announcement_Date (Optional[datetime]): DSO announcement date, should be in the future
        Package_Event_Type (Package_Event_Type): The event type of the package.
    """

    Bill_UUID: uuid.UUID
    Announcement_Date: Optional[datetime]
    Package_Event_Type: Package_Event_Type

    @validator("Announcement_Date", pre=False, always=True)
    def validate_effective_date(cls, v):
        if v is not None:
            effective_date = parse(v) if isinstance(v, str) else v
            if effective_date <= datetime.now(ZoneInfo("Europe/Amsterdam")):
                raise ValueError("Announcement Date must be in the future")
        return v


class CreatePublicationPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationPackageCreate,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            pub_object_repo: PublicationObjectRepository = Depends(depends_publication_object_repository),
            ow_object_repo: OWObjectRepository = Depends(depends_ow_object_repository),
            dso_service: DSOService = Depends(depends_dso_service),
        ) -> PublicationPackage:
            try:
                return self._handler(
                    object_in=object_in,
                    pub_repo=publication_repo,
                    dso_service=dso_service,
                    pub_object_repository=pub_object_repo,
                    ow_object_repo=ow_object_repo,
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

    def _handler(
        self,
        pub_repo: PublicationRepository,
        object_in: PublicationPackageCreate,
        pub_object_repository: PublicationObjectRepository,
        ow_object_repo: OWObjectRepository,
        dso_service: DSOService,
    ) -> PublicationPackage:
        """
        - Create new publication package using bill and config data
        - Call DSO Service build publication package files
        - Save filtered export state in DB
        - Save new OW objects in DB
        - Return package UUID

        Args:
            pub_repo (PublicationRepository): The repository for publication data.
            object_in (PublicationPackageCreate): The input data for creating a publication package.
            pub_object_repository (PublicationObjectRepository): The repository for publication objects.
            ow_object_repo (OWObjectRepository): The repository for OW objects.
            dso_service (DSOService): The DSO service.

        Returns:
            PublicationPackage: The response containing the UUID of the created publication package.
        """
        current_config: PublicationConfigTable = pub_repo.get_latest_config()
        if not current_config:
            raise MissingPublicationConfigError("No config found")
        current_config = PublicationConfig.from_orm(current_config)

        bill_db = pub_repo.get_publication_bill(uuid=object_in.Bill_UUID)
        if not bill_db:
            raise PublicationBillNotFound(f"Publication bill with UUID {object_in.Bill_UUID} not found")
        bill = PublicationBill.from_orm(bill_db)

        data = object_in.dict()
        new_package_db = PublicationPackageTable(
            UUID=uuid.uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Publication_Filename="akn_testfixture.xml",
            Province_ID=current_config.Province_ID,
            Submitter_ID=current_config.Submitter_ID,
            Authority_ID=current_config.Authority_ID,
            Jurisdiction=current_config.Jurisdiction,
            Subjects=current_config.Subjects,
            dso_stop_version=current_config.dso_stop_version,
            dso_tpod_version=current_config.dso_tpod_version,
            dso_bhkv_version=current_config.dso_bhkv_version,
            **data,
        )
        new_package_db = pub_repo.create_publication_package(new_package_db)
        package = PublicationPackage.from_orm(new_package_db)

        # Call DSO Service create package files
        objects = pub_object_repository.fetch_objects(
            module_id=bill.Module_ID,
            timepoint=datetime.utcnow(),
            object_types=[
                "visie_algemeen",
                "ambitie",
                "beleidsdoel",
                "beleidskeuze",
            ],
            field_map=[
                "UUID",
                "Object_Type",
                "Object_ID",
                "Code",
                "Hierarchy_Code",
                "Gebied_UUID",
                "Title",
                "Description",
                "Cause",
                "Provincial_Interest",
                "Explanation",
            ],
        )

        input_data = dso_service.prepare_publication_input(
            bill=bill,
            package=package,
            config=current_config,
            objects=objects,
        )

        # Start DSO module
        dso_service.build_dso_package(input_data)

        # Save state and new objects in DB
        state_exported = json.loads(dso_service.get_filtered_export_state())

        new_export = DSOStateExportTable(
            UUID=uuid.uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Package_UUID=package.UUID,
            Export_Data=state_exported,
        )
        new_export = pub_repo.create_dso_state_export(new_export)

        # Store new OW objects in DB
        ow_objects = create_ow_objects_from_json(
            exported_state=state_exported,
            package_uuid=package.UUID,
            bill_type=bill.Bill_Type,
        )
        ow_object_repo.create_ow_objects(ow_objects)

        return PublicationPackage.from_orm(new_package_db)


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
        return CreatePublicationPackageEndpoint(path=path)
