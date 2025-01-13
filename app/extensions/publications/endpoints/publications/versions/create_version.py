import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleStatusHistoryTable
from app.extensions.modules.dependencies import depends_module_status_repository
from app.extensions.modules.repository.module_status_repository import ModuleStatusRepository
from app.extensions.publications.dependencies import depends_publication, depends_publication_version_defaults_provider
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.publication_version_defaults_provider import (
    PublicationVersionDefaultsProvider,
)
from app.extensions.publications.tables.tables import PublicationTable, PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationVersionCreate(BaseModel):
    Module_Status_ID: int


class PublicationVersionCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        module_status_repository: ModuleStatusRepository,
        defaults_provider: PublicationVersionDefaultsProvider,
        user: UsersTable,
        publication: PublicationTable,
        object_in: PublicationVersionCreate,
    ):
        self._db: Session = db
        self._module_status_repository: ModuleStatusRepository = module_status_repository
        self._defaults_provider: PublicationVersionDefaultsProvider = defaults_provider
        self._user: UsersTable = user
        self._publication: PublicationTable = publication
        self._object_in: PublicationVersionCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> PublicationVersionCreatedResponse:
        self._guard_locked()

        module_status: ModuleStatusHistoryTable = self._get_module_status()

        bill_metadata = self._defaults_provider.get_bill_metadata(
            self._publication.Document_Type, self._publication.Procedure_Type
        )
        bill_compact = self._defaults_provider.get_bill_compact(
            self._publication.Document_Type, self._publication.Procedure_Type
        )
        procedural = self._defaults_provider.get_procedural()

        version: PublicationVersionTable = PublicationVersionTable(
            UUID=uuid.uuid4(),
            Publication_UUID=self._publication.UUID,
            Module_Status_ID=module_status.ID,
            Bill_Metadata=bill_metadata.dict(),
            Bill_Compact=bill_compact.dict(),
            Procedural=procedural.dict(),
            Effective_Date=None,
            Announcement_Date=None,
            Is_Locked=False,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(version)
        self._db.commit()
        self._db.flush()

        return PublicationVersionCreatedResponse(
            UUID=version.UUID,
        )

    def _guard_locked(self):
        if not self._publication.Act.Is_Active:
            raise HTTPException(status_code=409, detail="This act can no longer be used")

    def _get_module_status(self) -> ModuleStatusHistoryTable:
        module_status: Optional[ModuleStatusHistoryTable] = self._module_status_repository.get_by_id(
            self._publication.Module_ID,
            self._object_in.Module_Status_ID,
        )
        if module_status is None:
            raise HTTPException(status_code=404, detail="Module Status niet gevonden")

        return module_status


class CreatePublicationVersionEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationVersionCreate,
            publication: PublicationTable = Depends(depends_publication),
            module_status_repository: ModuleStatusRepository = Depends(depends_module_status_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_version,
                )
            ),
            defaults_provider: PublicationVersionDefaultsProvider = Depends(
                depends_publication_version_defaults_provider
            ),
            db: Session = Depends(depends_db),
        ) -> PublicationVersionCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                module_status_repository,
                defaults_provider,
                user,
                publication,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationVersionCreatedResponse,
            summary="Create new publication version",
            description=None,
            tags=["Publication Versions"],
        )

        return router


class CreatePublicationVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_version"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{publication_uuid}" in path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return CreatePublicationVersionEndpoint(path=path)
