import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core_old.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import (
    depends_act_defaults_provider,
    depends_publication_environment_repository,
)
from app.extensions.publications.enums import DocumentType, ProcedureType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.repository.publication_environment_repository import PublicationEnvironmentRepository
from app.extensions.publications.services.act_defaults_provider import ActDefaultsProvider
from app.extensions.publications.tables.tables import PublicationActTable, PublicationEnvironmentTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class ActCreate(BaseModel):
    Environment_UUID: uuid.UUID
    Document_Type: DocumentType
    Title: str
    Work_Other: Optional[str] = None


class ActCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        environment_repository: PublicationEnvironmentRepository,
        defaults_provider: ActDefaultsProvider,
        user: UsersTable,
        object_in: ActCreate,
    ):
        self._db: Session = db
        self._environment_repository: PublicationEnvironmentRepository = environment_repository
        self._defaults_provider: ActDefaultsProvider = defaults_provider
        self._user: UsersTable = user
        self._object_in: ActCreate = object_in
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> ActCreatedResponse:
        environment: PublicationEnvironmentTable = self._get_environment()

        metadata = self._defaults_provider.get_metadata(self._object_in.Document_Type.value)
        work_other: str = self._object_in.Work_Other or self._get_work_other()

        act: PublicationActTable = PublicationActTable(
            UUID=uuid.uuid4(),
            Environment_UUID=environment.UUID,
            Document_Type=self._object_in.Document_Type.value,
            Title=self._object_in.Title,
            Is_Active=True,
            Metadata=metadata.model_dump(),
            Metadata_Is_Locked=False,
            Work_Province_ID=environment.Province_ID,
            Work_Country=environment.Frbr_Country,
            Work_Date=str(self._timepoint.year),
            Work_Other=work_other,
            Withdrawal_Purpose_UUID=None,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )

        self._db.add(act)
        self._db.commit()
        self._db.flush()

        return ActCreatedResponse(
            UUID=act.UUID,
        )

    def _get_environment(self) -> PublicationEnvironmentTable:
        environment: Optional[PublicationEnvironmentTable] = self._environment_repository.get_by_uuid(
            self._object_in.Environment_UUID,
        )
        if environment is None:
            raise HTTPException(status_code=404, detail="Publication Environment niet gevonden")
        if not environment.Is_Active:
            raise HTTPException(status_code=404, detail="Publication Environment is in actief")

        return environment

    def _get_work_other(self) -> str:
        stmt = (
            select(func.count())
            .select_from(PublicationActTable)
            .filter(PublicationActTable.Environment_UUID == self._object_in.Environment_UUID)
            .filter(PublicationActTable.Document_Type == self._object_in.Document_Type.value)
            .filter(
                or_(
                    PublicationActTable.Procedure_Type == ProcedureType.FINAL,
                    PublicationActTable.Procedure_Type == None,
                ).self_group()
            )
        )
        count: int = self._db.execute(stmt).scalar() + 1
        id_suffix: str = f"{count}"

        work_other: str = f"{self._object_in.Document_Type.value.lower()}-{id_suffix}"
        return work_other


class CreateActEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ActCreate,
            environment_repository: PublicationEnvironmentRepository = Depends(
                depends_publication_environment_repository
            ),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_create_publication_act,
                )
            ),
            defaults_provider: ActDefaultsProvider = Depends(depends_act_defaults_provider),
            db: Session = Depends(depends_db),
        ) -> ActCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                environment_repository,
                defaults_provider,
                user,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ActCreatedResponse,
            summary="Create new Act",
            description=None,
            tags=["Publication Acts"],
        )

        return router


class CreateActEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_act"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return CreateActEndpoint(path=path)
