import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import validators
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db, depends_security
from app.core.security import Security
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.users.db.tables import IS_ACTIVE, UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
    depends_user_repository,
)
from app.extensions.users.permissions import UserManagementPermissions
from app.extensions.users.repository.user_repository import UserRepository


class UserCreate(BaseModel):
    Gebruikersnaam: str = Field(..., min_length=3)
    Email: str
    Rol: str

    @field_validator("Email", mode="before")
    def valid_email(cls, v):
        if not validators.email(v):
            raise ValueError("Invalid email")
        return v


class UserCreateResponse(BaseModel):
    UUID: uuid.UUID
    Email: str
    Rol: str
    Password: str


class CreateUserEndpointHandler:
    def __init__(
        self,
        db: Session,
        security: Security,
        repository: UserRepository,
        allowed_roles: List[str],
        logged_in_user: UsersTable,
        object_in: UserCreate,
    ):
        self._db: Session = db
        self._security: Security = security
        self._repository: UserRepository = repository
        self._allowed_roles: List[str] = allowed_roles
        self._logged_in_user: UsersTable = logged_in_user
        self._object_in: UserCreate = object_in

    def handle(self) -> UserCreateResponse:
        if self._object_in.Rol not in self._allowed_roles:
            raise ValueError("Invalid Rol")

        same_email_user: Optional[UsersTable] = self._repository.get_by_email(self._object_in.Email)
        if same_email_user:
            raise ValueError(f"Email already in use")

        password = "change-me-" + self._security.get_random_password()
        password_hash = self._security.get_password_hash(password)

        user: UsersTable = UsersTable(
            UUID=uuid.uuid4(),
            Gebruikersnaam=self._object_in.Gebruikersnaam,
            Email=self._object_in.Email,
            Rol=self._object_in.Rol,
            Status=IS_ACTIVE,
            Wachtwoord=password_hash,
        )

        change_log: ChangeLogTable = ChangeLogTable(
            Created_Date=datetime.now(timezone.utc),
            Created_By_UUID=self._logged_in_user.UUID,
            Action_Type="create_user",
            Action_Data=self._object_in.json(),
            After=json.dumps(user.to_dict_safe()),
        )

        self._db.add(change_log)
        self._db.add(user)
        self._db.flush()
        self._db.commit()

        return UserCreateResponse(
            UUID=user.UUID,
            Email=user.Email,
            Rol=user.Rol,
            Password=password,
        )


class CreateUserEndpoint(Endpoint):
    def __init__(self, path: str, allowed_roles: List[str]):
        self._path: str = path
        self._allowed_roles: List[str] = allowed_roles

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: UserCreate,
            logged_in_user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(UserManagementPermissions.can_create_user),
            ),
            db: Session = Depends(depends_db),
            repository: UserRepository = Depends(depends_user_repository),
            security: Security = Depends(depends_security),
        ) -> UserCreateResponse:
            handler: CreateUserEndpointHandler = CreateUserEndpointHandler(
                db,
                security,
                repository,
                self._allowed_roles,
                logged_in_user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=UserCreateResponse,
            summary=f"Create new user",
            description=None,
            tags=["User"],
        )

        return router


class CreateUserEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_user"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        allowed_roles: List[str] = resolver_config.get("allowed_roles")

        return CreateUserEndpoint(path=path, allowed_roles=allowed_roles)
