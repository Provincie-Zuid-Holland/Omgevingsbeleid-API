import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.publications.dependencies import depends_package_builder_factory, depends_publication_version
from app.extensions.publications.enums import PackageType
from app.extensions.publications.permissions import PublicationsPermissions
from app.extensions.publications.services.package_builder import PackageBuilder
from app.extensions.publications.services.package_builder_factory import PackageBuilderFactory
from app.extensions.publications.tables.tables import PublicationVersionTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user_with_permission_curried


class PublicationPackageCreate(BaseModel):
    Package_Type: PackageType


class PublicationPackageCreatedResponse(BaseModel):
    UUID: uuid.UUID


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        package_builder_factory: PackageBuilderFactory,
        user: UsersTable,
        object_in: PublicationPackageCreate,
        publication_version: PublicationVersionTable,
    ):
        self._db: Session = db
        self._package_builder_factory: PackageBuilderFactory = package_builder_factory
        self._user: UsersTable = user
        self._object_in: PublicationPackageCreate = object_in
        self._publication_version: PublicationVersionTable = publication_version
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> PublicationPackageCreatedResponse:
        self._guard_validate_package_type()

        builder: PackageBuilder = self._package_builder_factory.create_builder(
            self._publication_version,
            self._object_in.Package_Type,
        )
        builder.build()

        a = True

    def _guard_validate_package_type(self):
        match self._object_in.Package_Type:
            case PackageType.TERMINATE:
                raise NotImplementedError("Afbreek verzoek is nog niet geimplementeerd")
            case PackageType.VALIDATION:
                if not self._publication_version.Environment.Can_Validate:
                    raise HTTPException("Can not create Validation for this environment")
            case PackageType.PUBLICATION:
                if not self._publication_version.Environment.Can_Publicate:
                    raise HTTPException("Can not create Publication for this environment")


class CreatePublicationPackageEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: PublicationPackageCreate,
            publication_version: PublicationVersionTable = Depends(depends_publication_version),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    PublicationsPermissions.can_view_publication_version,
                )
            ),
            package_builder_factory: PackageBuilderFactory = Depends(depends_package_builder_factory),
            db: Session = Depends(depends_db),
        ) -> PublicationPackageCreatedResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                package_builder_factory,
                user,
                object_in,
                publication_version,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=PublicationPackageCreatedResponse,
            summary="Create new Publication Package",
            tags=["Publications", "Publication Packages"],
        )

        return router


class CreatePublicationPackageEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "create_publication_package"

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

        if not "{version_uuid}" in path:
            raise RuntimeError("Missing {version_uuid} argument in path")

        return CreatePublicationPackageEndpoint(path=path)
