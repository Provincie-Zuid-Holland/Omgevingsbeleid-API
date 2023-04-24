from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.dependencies import depends_db
from sqlalchemy.orm import Session

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.regulations.db.tables import RegulationsTable
from app.extensions.regulations.dependencies import depends_regulation
from app.extensions.regulations.models.models import RegulationTypes
from app.extensions.regulations.permissions import RegulationsPermissions
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
)


class RegulationEdit(BaseModel):
    Title: str = Field(..., min_length=3)
    Type: RegulationTypes


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        regulation: RegulationsTable,
        object_in: RegulationEdit,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._regulation: RegulationsTable = regulation
        self._object_in: RegulationEdit = object_in

    def handle(self) -> ResponseOK:
        changes: dict = self._object_in.dict(exclude_none=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            setattr(self._regulation, key, value)

        self._regulation.Modified_By_UUID = self._user.UUID
        self._regulation.Modified_Date = datetime.now()

        self._db.add(self._regulation)
        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )


class EditRegulationEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: RegulationEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    RegulationsPermissions.can_edit_regulation
                ),
            ),
            regulation: RegulationsTable = Depends(depends_regulation),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                regulation,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit regulation",
            description=None,
            tags=["Regulations"],
        )

        return router


class EditRegulationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_regulation"

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
        if not "{regulation_uuid}" in path:
            raise RuntimeError("Missing {regulation_uuid} argument in path")

        return EditRegulationEndpoint(
            path=path,
        )
