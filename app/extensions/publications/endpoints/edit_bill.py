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
from app.extensions.publications.dependencies import depends_publication_repository
from app.extensions.publications.exceptions import PublicationBillNotFound
from app.extensions.publications.helpers import serialize_datetime
from app.extensions.publications.models import Bill_Data, Procedure_Data, PublicationBill
from app.extensions.publications.repository import PublicationRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicationBillEdit(BaseModel):
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


class EditPublicationBillEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            bill_uuid: uuid.UUID,
            object_in: PublicationBillEdit,
            publication_repo: PublicationRepository = Depends(depends_publication_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> PublicationBill:
            return self._handler(bill_uuid=bill_uuid, object_in=object_in, repo=publication_repo)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PATCH"],
            response_model=PublicationBill,
            summary="Edit an existing publication Bill or version",
            description=None,
            tags=["Publications"],
        )

        return router

    def _handler(
        self, bill_uuid: uuid.UUID, repo: PublicationRepository, object_in: PublicationBillEdit
    ) -> PublicationBill:
        # TODO: ensure effective date gap is not bypassed
        data = object_in.dict()
        data["Bill_Data"] = serialize_datetime(data["Bill_Data"])
        data["Procedure_Data"] = serialize_datetime(data["Procedure_Data"])

        # Only update provided fields that are not None
        data = {k: v for k, v in data.items() if v is not None}

        try:
            result = repo.update_publication_bill(bill_uuid, **data)
        except PublicationBillNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))

        return PublicationBill.from_orm(result)


class EditPublicationBillEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_bill"

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
        return EditPublicationBillEndpoint(path=path)
