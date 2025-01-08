from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_publication_version, depends_publication_version_validator
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.tables.tables import PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried
from app.dynamic.utils.response import ResponseOK


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        version: PublicationVersionTable,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._version: PublicationVersionTable = version

    def handle(self) -> ResponseOK:
        if self._version.Deleted_At is not None:
            raise HTTPException(status_code=400, detail="Publication Version already deleted")
        
        if self._version.Act_Packages:
            raise HTTPException(status_code=400, detail="Publication Version has related Act Packages, cannot delete")

        self._version.Deleted_At = datetime.now(tz=timezone.utc)
        self._version.Modified_By_UUID = self._user.UUID
        self._version.Modified_Date = datetime.now(tz=timezone.utc)

        self._db.add(self._version)
        self._db.commit()
        self._db.flush()

        return ResponseOK(
            message="OK",
        )


class DeletePublicationVersionEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_edit_publication_version,
                ),
            ),
            version: PublicationVersionTable = Depends(depends_publication_version),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                version,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary="Mark a publication version as deleted",
            description="Marks a publication version as deleted by setting its Deleted_At timestamp.",
            tags=["Publication Versions"],
        )

        return router


class DeletePublicationVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "delete_publication_version"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return DeletePublicationVersionEndpoint(path=path)
