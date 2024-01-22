from datetime import datetime
from typing import Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.enums import Bill_Type, Document_Type
from app.extensions.publications.helpers import serialize_datetime
from app.extensions.publications.models import Bill_Data, Procedure_Data
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.tables import PublicationBillTable


class PublicationBillCreate(BaseModel):
    Module_ID: int
    Module_Status_ID: int
    Document_Type: Document_Type
    Bill_Type: Bill_Type
    Effective_Date: Optional[datetime]
    Announcement_Date: Optional[datetime]
    Bill_Data: Optional[Bill_Data]
    Procedure_Data: Optional[Procedure_Data]

    @validator("Effective_Date", pre=False, always=True)
    def validate_effective_date(cls, v):
        if v is not None:
            effective_date = parse(v) if isinstance(v, str) else v
            if effective_date <= datetime.now(ZoneInfo("Europe/Amsterdam")):
                raise ValueError("Effective Date must be in the future")
        return v

    @validator("Announcement_Date", pre=False, always=True)
    def validate_announcement_date(cls, v, values, **kwargs):
        if "Effective_Date" in values and v is not None:
            announcement_date = parse(v) if isinstance(v, str) else v
            effective_date = (
                parse(values["Effective_Date"])
                if isinstance(values["Effective_Date"], str)
                else values["Effective_Date"]
            )
            if effective_date is not None and announcement_date >= effective_date:
                raise ValueError("Announcement Date must be earlier than Effective Date")

            if announcement_date <= datetime.now(ZoneInfo("Europe/Amsterdam")):
                raise ValueError("Announcement Date must in the future")

        return v


class PublicationBillResponse(BaseModel):
    Version_ID: int


class CreatePublicationBillEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            # user: UsersTable = Depends(depends_current_active_user),
            object_in: PublicationBillCreate,
            bill_repository: PublicationRepository = Depends(depends_publication_repository),
        ) -> PublicationBillResponse:
            return self._handler(object_in=object_in, bill_repo=bill_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationBillResponse,
            summary="Create new publication Bills",
            description=None,
            tags=["Publications"],
        )

        return router

    def _handler(self, bill_repo: PublicationRepository, object_in: PublicationBillCreate) -> PublicationBillResponse:
        """
        Handles the creation of a publication bill.

        Args:
            bill_repo (PublicationRepository): The repository for publication bills.
            object_in (PublicationBillCreate): The input data for creating a publication bill.

        Returns:
            PublicationBillResponse: The response containing the version ID of the created publication bill.
        """
        data = object_in.dict()
        data["Bill_Data"] = serialize_datetime(data["Bill_Data"])
        data["Procedure_Data"] = serialize_datetime(data["Procedure_Data"])
        new_bill = PublicationBillTable(UUID=uuid4(), Created_Date=datetime.now(), Modified_Date=datetime.now(), **data)
        result = bill_repo.create_publication_bill(new_bill)

        return PublicationBillResponse(Version_ID=result.Version_ID)


class CreatePublicationBillEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_bill"

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
        return CreatePublicationBillEndpoint(path=path)
