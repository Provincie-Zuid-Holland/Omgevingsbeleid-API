import uuid
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
from app.extensions.publications.enums import Procedure_Type
from app.extensions.publications.helpers import serialize_datetime
from app.extensions.publications.models import Bill_Data, Procedure_Data, PublicationBill
from app.extensions.publications.repository import PublicationRepository
from app.extensions.publications.tables import PublicationBillTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationBillCreate(BaseModel):
    Module_Status_ID: int
    Procedure_Type: Procedure_Type
    Is_Official: bool
    Effective_Date: Optional[datetime]
    Announcement_Date: Optional[datetime]
    PZH_Bill_Identifier: Optional[str]
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


class CreatePublicationBillEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            publication_uuid: uuid.UUID,
            object_in: PublicationBillCreate,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PublicationBill:
            return self._handler(object_in=object_in, repo=publication_repo, publication_uuid=publication_uuid)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationBill,
            summary="Create new publication Bill or version",
            description=None,
            tags=["Publications"],
        )

        return router

    def _handler(
        self, repo: PublicationRepository, object_in: PublicationBillCreate, publication_uuid: uuid.UUID
    ) -> PublicationBill:
        data = object_in.dict()
        data["Bill_Data"] = serialize_datetime(data["Bill_Data"])
        data["Procedure_Data"] = serialize_datetime(data["Procedure_Data"])
        new_bill = PublicationBillTable(
            UUID=uuid4(),
            Created_Date=datetime.now(),
            Modified_Date=datetime.now(),
            Publication_UUID=publication_uuid,
            **data
        )
        result = repo.create_publication_bill(new_bill)
        return PublicationBill.from_orm(result)


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

        if not "{publication_uuid}" in path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return CreatePublicationBillEndpoint(path=path)
