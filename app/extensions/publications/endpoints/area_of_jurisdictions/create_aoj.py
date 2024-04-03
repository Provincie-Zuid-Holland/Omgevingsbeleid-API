import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationAreaOfJurisdictionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class AOJCreate(BaseModel):
    Administrative_Borders_ID: str = Field(..., min_length=3)
    Administrative_Borders_Domain: str = Field(..., min_length=3)
    Administrative_Borders_Date: date


class AOJCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_in: AOJCreate,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_in: AOJCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> AOJCreatedResponse:
        area_of_jurisdiction: PublicationAreaOfJurisdictionTable = PublicationAreaOfJurisdictionTable(
            UUID=uuid.uuid4(),
            Administrative_Borders_ID=self._object_in.Administrative_Borders_ID,
            Administrative_Borders_Domain=self._object_in.Administrative_Borders_Domain,
            Administrative_Borders_Date=self._object_in.Administrative_Borders_Date,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )

        self._db.add(area_of_jurisdiction)

        self._db.flush()
        self._db.commit()

        return AOJCreatedResponse(
            UUID=area_of_jurisdiction.UUID,
        )


class CreatePublicationAOJEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: AOJCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(PublicationsPermissions.can_create_publication_aoj),
            ),
            db: Session = Depends(depends_db),
        ) -> AOJCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=AOJCreatedResponse,
            summary=f"Create new publication area of jurisdictions",
            description=None,
            tags=["Publication AOJ"],
        )

        return router


class CreatePublicationAOJEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_area_of_jurisdictions"

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

        return CreatePublicationAOJEndpoint(path=path)
