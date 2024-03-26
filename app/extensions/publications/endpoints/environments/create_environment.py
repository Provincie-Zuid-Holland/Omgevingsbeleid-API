import uuid
from datetime import datetime

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
from app.extensions.publications.services.state.state import InitialState
from app.extensions.publications.tables.tables import PublicationEnvironmentStateTable, PublicationEnvironmentTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class EnvironmentCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Description: str
    Province_ID: str
    Authority_ID: str
    Submitter_ID: str
    Frbr_Country: str
    Frbr_Language: str
    Has_State: bool
    Can_Validate: bool
    Can_Publicate: bool


class EnvironmentCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_in: EnvironmentCreate,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_in: EnvironmentCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> EnvironmentCreatedResponse:
        environment: PublicationEnvironmentTable = PublicationEnvironmentTable(
            UUID=uuid.uuid4(),
            Title=self._object_in.Title,
            Description=self._object_in.Description,
            Province_ID=self._object_in.Province_ID,
            Authority_ID=self._object_in.Authority_ID,
            Submitter_ID=self._object_in.Submitter_ID,
            Governing_Body_Type="provinciale_staten",
            Frbr_Country=self._object_in.Frbr_Country,
            Frbr_Language=self._object_in.Frbr_Language,
            Is_Active=True,
            Has_State=self._object_in.Has_State,
            Can_Validate=self._object_in.Can_Validate,
            Can_Publicate=self._object_in.Can_Publicate,
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(environment)
        self._db.flush()

        if environment.Has_State:
            initial_state: PublicationEnvironmentStateTable = PublicationEnvironmentStateTable(
                UUID=uuid.uuid4(),
                Environment_UUID=environment.UUID,
                Adjust_On_UUID=None,
                State=(InitialState().state_dict()),
                Is_Activated=True,
                Activated_Datetime=self._timepoint,
                Created_Date=self._timepoint,
                Created_By_UUID=self._user.UUID,
            )
            self._db.add(initial_state)

        self._db.flush()
        self._db.commit()

        return EnvironmentCreatedResponse(
            UUID=environment.UUID,
        )


class CreatePublicationEnvironmentEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: EnvironmentCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_environment
                ),
            ),
            db: Session = Depends(depends_db),
        ) -> EnvironmentCreatedResponse:
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
            response_model=EnvironmentCreatedResponse,
            summary=f"Create new publication environment",
            description=None,
            tags=["Publication Environments"],
        )

        return router


class CreatePublicationEnvironmentEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_environment"

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

        return CreatePublicationEnvironmentEndpoint(path=path)
