from datetime import datetime
from typing import Optional, List
import uuid
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from dateutil.parser import parse

from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.event_dispatcher import EventDispatcher
from app.extensions.publications import (
    PublicationPackageTable,
    Package_Event_Type,
    MissingPublicationConfigError,
    PublicationPackage,
)
from app.extensions.publications.exceptions import PublicationBillNotFound
from app.extensions.publications.models import PublicationConfig
from app.extensions.publications.repository.publication_repository import PublicationRepository
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.tables import PublicationConfigTable


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
        ) -> PublicationPackage:
            try:
                return self._handler(object_in=object_in, pub_repo=publication_repo)
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
        self, pub_repo: PublicationRepository, object_in: PublicationPackageCreate
    ) -> PublicationPackage:
        """
        Find the current set config values and handles the creation of a publication package.

        Args:
            pub_repo (PublicationRepository): The repository for publication data.
            object_in (PublicationPackageCreate): The input data for creating a publication package.

        Returns:
            PublicationPackage: The response containing the UUID of the created publication package.
        """
        current_config: PublicationConfigTable = pub_repo.fetch_latest_config()
        if not current_config:
            raise MissingPublicationConfigError("No config found")

        bill = pub_repo.get_publication_bill(uuid=object_in.Bill_UUID)
        if not bill:
            raise PublicationBillNotFound(
                f"Publication bill with UUID {object_in.Bill_UUID} not found"
            )

        data = object_in.dict()
        new_package = PublicationPackageTable(
            UUID=uuid.uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Province_ID=current_config.Province_ID,
            Submitter_ID=current_config.Submitter_ID,
            Authority_ID=current_config.Authority_ID,
            Jurisdiction=current_config.Jurisdiction,
            Subjects=current_config.Subjects,
            dso_stop_version=current_config.dso_stop_version,
            dso_tpod_version=current_config.dso_tpod_version,
            dso_bhkv_version=current_config.dso_bhkv_version,
            **data
        )
        result = pub_repo.create_publication_package(new_package)
        return PublicationPackage.from_orm(result)


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
