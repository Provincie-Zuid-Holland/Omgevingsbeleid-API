from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

from app.core.dependencies import depends_db
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.regulations.db.tables import RegulationsTable
from app.extensions.regulations.models.models import RegulationTypes
from app.extensions.regulations.permissions import RegulationsPermissions
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
)


class RegulationCreate(BaseModel):
    Title: str = Field(..., min_length=3)
    Type: RegulationTypes


class RegulationCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_in: RegulationCreate,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_in: RegulationCreate = object_in
        self._timepoint: datetime = datetime.now()

    def handle(self) -> RegulationCreatedResponse:
        regulation: RegulationsTable = RegulationsTable(
            UUID=uuid.uuid4(),
            Title=self._object_in.Title,
            Type=self._object_in.Type,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(regulation)
        self._db.flush()
        self._db.commit()

        return RegulationCreatedResponse(
            UUID=regulation.UUID,
        )


class CreateRegulationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: RegulationCreate,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    RegulationsPermissions.can_create_regulation
                ),
            ),
            db: Session = Depends(depends_db),
        ) -> RegulationCreatedResponse:
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
            response_model=RegulationCreatedResponse,
            summary=f"Create new regulation",
            description=None,
            tags=["Regulations"],
        )

        return router


class CreateRegulationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_regulation"

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

        return CreateRegulationEndpoint(path=path)
