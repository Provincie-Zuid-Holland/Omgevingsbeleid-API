import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleStatusHistoryTable
from app.extensions.modules.dependencies import depends_module_status_repository
from app.extensions.modules.repository.module_status_repository import ModuleStatusRepository
from app.extensions.publications.dependencies import (
    depends_package_version_defaults_provider,
    depends_publication,
    depends_publication_environment_repository,
)
from app.extensions.publications.enums import ProcedureType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.extensions.publications.services.package_version_defaults_provider import PackageVersionDefaultsProvider
from app.extensions.publications.tables.tables import (
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationVersionTable,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationVersionCreate(BaseModel):
    Module_Status_ID: int
    Environment_UUID: uuid.UUID


class PublicationVersionCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        environment_repository: PublicationEnvironmentRepository,
        module_status_repository: ModuleStatusRepository,
        defaults_provider: PackageVersionDefaultsProvider,
        user: UsersTable,
        publication: PublicationTable,
        object_in: PublicationVersionCreate,
    ):
        self._db: Session = db
        self._environment_repository: PublicationEnvironmentRepository = environment_repository
        self._module_status_repository: ModuleStatusRepository = module_status_repository
        self._defaults_provider: PackageVersionDefaultsProvider = defaults_provider
        self._user: UsersTable = user
        self._publication: PublicationTable = publication
        self._object_in: PublicationVersionCreate = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> PublicationVersionCreatedResponse:
        module_status: ModuleStatusHistoryTable = self._get_module_status()
        environment: PublicationEnvironmentTable = self._get_environment()

        bill_metadata = self._defaults_provider.get_bill_metadata(self._publication.Document_Type)
        bill_compact = self._defaults_provider.get_bill_compact(self._publication.Document_Type)
        procedural = self._defaults_provider.get_procedural()
        act_metadata = self._defaults_provider.get_act_metadata(self._publication.Document_Type)

        version: PublicationVersionTable = PublicationVersionTable(
            UUID=uuid.uuid4(),
            Publication_UUID=self._publication.UUID,
            Module_Status_ID=module_status.ID,
            Environment_UUID=environment.UUID,
            Procedure_Type=ProcedureType.FINAL,
            Bill_Metadata=bill_metadata.dict(),
            Bill_Compact=bill_compact.dict(),
            Procedural=procedural.dict(),
            Act_Metadata=act_metadata.dict(),
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

    def _get_module_status(self) -> ModuleStatusHistoryTable:
        module_status: Optional[ModuleStatusHistoryTable] = self._module_status_repository.get_by_id(
            self._publication.Module_ID,
            self._object_in.Module_Status_ID,
        )
        if module_status is None:
            raise HTTPException(status_code=404, detail="Module Status niet gevonden")

        return module_status

    def _get_environment(self) -> PublicationEnvironmentTable:
        environment: Optional[PublicationEnvironmentTable] = self._environment_repository.get_by_uuid(
            self._object_in.Environment_UUID,
        )
        if environment is None:
            raise HTTPException(status_code=404, detail="Publication Environment niet gevonden")
        if not environment.Is_Active:
            raise HTTPException(status_code=404, detail="Publication Environment is in actief")

        return environment


class CreatePublicationVersionEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationVersionCreate,
            publication: PublicationTable = Depends(depends_publication),
            environment_repository: PublicationEnvironmentRepository = Depends(
                depends_publication_environment_repository
            ),
            module_status_repository: ModuleStatusRepository = Depends(depends_module_status_repository),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_version,
                )
            ),
            defaults_provider: PackageVersionDefaultsProvider = Depends(depends_package_version_defaults_provider),
            db: Session = Depends(depends_db),
        ) -> PublicationVersionCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                environment_repository,
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
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        if not "{publication_uuid}" in path:
            raise RuntimeError("Missing {publication_uuid} argument in path")

        return CreatePublicationVersionEndpoint(path=path)
