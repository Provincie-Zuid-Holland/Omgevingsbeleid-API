import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.core.security import get_password_hash, get_random_password
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
    depends_user_repository,
)
from app.extensions.users.permissions import UserManagementPermissions
from app.extensions.users.repository.user_repository import UserRepository


class ResetPasswordResponse(BaseModel):
    UUID: uuid.UUID
    NewPassword: str


class ResetUserPasswordEndpointHandler:
    def __init__(self, db: Session, repository: UserRepository, logged_in_user: UsersTable, user_uuid: uuid.UUID):
        self._db: Session = db
        self._repository: UserRepository = repository
        self._logged_in_user: UsersTable = logged_in_user
        self._user_uuid: uuid.UUID = user_uuid
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> ResetPasswordResponse:
        user: Optional[UsersTable] = self._repository.get_by_uuid(self._user_uuid)
        if not user:
            raise ValueError(f"User does not exist")
        if not user.Is_Active:
            raise ValueError(f"User is inactive")

        password = "change-me-" + get_random_password()
        password_hash = get_password_hash(password)

        user.Wachtwoord = password_hash

        change_log: ChangeLogTable = ChangeLogTable(
            Created_Date=self._timepoint,
            Created_By_UUID=self._logged_in_user.UUID,
            Action_Type="reset_user_password",
            Action_Data=json.dumps({"UUID": str(user.UUID)}),
        )

        self._db.add(change_log)
        self._db.add(user)
        self._db.flush()
        self._db.commit()

        return ResetPasswordResponse(
            UUID=user.UUID,
            NewPassword=password,
        )


class ResetUserPasswordEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user_uuid: uuid.UUID,
            logged_in_user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(UserManagementPermissions.can_reset_user_password),
            ),
            db: Session = Depends(depends_db),
            repository: UserRepository = Depends(depends_user_repository),
        ) -> ResetPasswordResponse:
            handler: ResetUserPasswordEndpointHandler = ResetUserPasswordEndpointHandler(
                db,
                repository,
                logged_in_user,
                user_uuid,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResetPasswordResponse,
            summary=f"Reset user password",
            description=None,
            tags=["User"],
        )

        return router


class ResetUserPasswordEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "reset_user_password"

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
        if not "{user_uuid}" in path:
            raise RuntimeError("Missing {user_uuid} argument in path")

        return ResetUserPasswordEndpoint(path)
