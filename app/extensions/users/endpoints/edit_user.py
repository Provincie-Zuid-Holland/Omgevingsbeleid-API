import json
import uuid
from datetime import datetime
from typing import List, Optional

import validators
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
    depends_user_repository,
)
from app.extensions.users.permissions import UserManagementPermissions
from app.extensions.users.repository.user_repository import UserRepository


class EditUser(BaseModel):
    Gebruikersnaam: Optional[str] = Field(None, nullable=True)
    Email: Optional[str] = Field(None, nullable=True)
    Rol: Optional[str] = Field(None, nullable=True)


class EditUserEndpointHandler:
    def __init__(
        self,
        db: Session,
        repository: UserRepository,
        logged_in_user: UsersTable,
        user_uuid: uuid.UUID,
        allowed_roles: List[str],
        object_in: EditUser,
    ):
        self._db: Session = db
        self._repository: UserRepository = repository
        self._logged_in_user: UsersTable = logged_in_user
        self._user_uuid: uuid.UUID = user_uuid
        self._allowed_roles: List[str] = allowed_roles
        self._object_in: EditUser = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self):
        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        user: Optional[UsersTable] = self._repository.get_by_uuid(self._user_uuid)
        if not user:
            raise ValueError(f"User does not exist")

        if self._object_in.Email:
            same_email_user: Optional[UsersTable] = self._repository.get_by_email(self._object_in.Email)
            if same_email_user and same_email_user.UUID != user.UUID:
                raise ValueError(f"Email already in use")

        user_before_dict: dict = user.to_dict_safe()
        log_before: str = json.dumps(user_before_dict)
        for key, value in changes.items():
            setattr(user, key, value)

        # This executes the validators on the result type
        # Making sure the final object meets all validation requirements
        if not validators.email(user.Email):
            raise ValueError("Invalid email")
        if user.Rol not in self._allowed_roles:
            raise ValueError("Invalid Rol")

        user_after_dict: dict = user.to_dict_safe()

        change_log: ChangeLogTable = ChangeLogTable(
            Created_Date=self._timepoint,
            Created_By_UUID=self._logged_in_user.UUID,
            Action_Type="edit_user",
            Action_Data=self._object_in.json(),
            Before=log_before,
            After=json.dumps(user_after_dict),
        )

        self._db.add(change_log)
        self._db.add(user)
        self._db.flush()
        self._db.commit()

        return ResponseOK(message="OK")


class EditUserEndpoint(Endpoint):
    def __init__(self, path: str, allowed_roles: List[str]):
        self._path: str = path
        self._allowed_roles: List[str] = allowed_roles

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user_uuid: uuid.UUID,
            object_in: EditUser,
            logged_in_user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(UserManagementPermissions.can_edit_user),
            ),
            db: Session = Depends(depends_db),
            repository: UserRepository = Depends(depends_user_repository),
        ) -> ResponseOK:
            handler: EditUserEndpointHandler = EditUserEndpointHandler(
                db,
                repository,
                logged_in_user,
                user_uuid,
                self._allowed_roles,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit user",
            description=None,
            tags=["User"],
        )

        return router


class EditUserEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_user"

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
        allowed_roles: List[str] = resolver_config.get("allowed_roles")

        return EditUserEndpoint(path, allowed_roles)
