from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.publications.dependencies import depends_publication_environment
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationEnvironmentTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class EnvironmentEdit(BaseModel):
    Title: Optional[str] = Field(None, nullable=True)
    Description: Optional[str] = Field(None, nullable=True)

    Province_ID: Optional[str] = Field(None, nullable=True)
    Authority_ID: Optional[str] = Field(None, nullable=True)
    Submitter_ID: Optional[str] = Field(None, nullable=True)

    Frbr_Country: Optional[str] = Field(None, nullable=True)
    Frbr_Language: Optional[str] = Field(None, nullable=True)

    Is_Active: Optional[bool] = Field(None, nullable=True)
    Can_Validate: Optional[bool] = Field(None, nullable=True)
    Can_Publicate: Optional[bool] = Field(None, nullable=True)


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        environment: PublicationEnvironmentTable,
        object_in: EnvironmentEdit,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._environment: PublicationEnvironmentTable = environment
        self._object_in: EnvironmentEdit = object_in

    def handle(self) -> ResponseOK:
        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        for key, value in changes.items():
            setattr(self._environment, key, value)

        self._environment.Modified_By_UUID = self._user.UUID
        self._environment.Modified_Date = datetime.utcnow()

        self._db.add(self._environment)
        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )


class EditPublicationEnvironmentEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: EnvironmentEdit,
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_environment
                ),
            ),
            environment: PublicationEnvironmentTable = Depends(depends_publication_environment),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                environment,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit publication environment",
            description=None,
            tags=["Publication Environments"],
        )

        return router


class EditPublicationEnvironmentEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_publication_environment"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{environment_uuid}" in path:
            raise RuntimeError("Missing {environment_uuid} argument in path")

        return EditPublicationEnvironmentEndpoint(
            path=path,
        )
