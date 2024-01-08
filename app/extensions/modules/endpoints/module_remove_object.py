from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.dependencies import depends_object_static_by_object_type_and_id
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context,
    depends_module_object_repository,
)
from app.extensions.modules.permissions import ModulesPermissions, guard_module_not_locked, guard_valid_user
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_permission_service
from app.extensions.users.permission_service import PermissionService


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        permission_service: PermissionService,
        module_object_repository: ModuleObjectRepository,
        user: UsersTable,
        module: ModuleTable,
        object_context: ModuleObjectContextTable,
        object_static: ObjectStaticsTable,
    ):
        self._db: Session = db
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._permission_service: PermissionService = permission_service
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._object_context: ModuleObjectContextTable = object_context
        self._object_static: ObjectStaticsTable = object_static
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> ResponseOK:
        guard_valid_user(
            self._permission_service,
            ModulesPermissions.can_remove_object_from_module,
            self._user,
            self._module,
        )
        guard_module_not_locked(self._module)

        self._flag_context_as_hidden()
        self._patch_module_object_as_deleted()

        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )

    def _flag_context_as_hidden(self):
        self._object_context.Hidden = True
        self._object_context.Modified_By_UUID = self._user.UUID
        self._object_context.Modified_Date = self._timepoint
        self._db.add(self._object_context)

    def _patch_module_object_as_deleted(self):
        new_record: ModuleObjectsTable = self._module_object_repository.patch_latest_module_object(
            self._object_context.Module_ID,
            self._object_context.Object_Type,
            self._object_context.Object_ID,
            {
                "Deleted": True,
            },
            self._timepoint,
            self._user.UUID,
        )
        self._db.add(new_record)


class ModuleRemoveObjectEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            object_context: ModuleObjectContextTable = Depends(depends_active_module_object_context),
            object_static: ObjectStaticsTable = Depends(
                depends_object_static_by_object_type_and_id,
            ),
            db: Session = Depends(depends_db),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            permission_service: PermissionService = Depends(depends_permission_service),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                permission_service,
                module_object_repository,
                user,
                module,
                object_context,
                object_static,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary=f"Remove object from the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleRemoveObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_remove_object"

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
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{object_type}" in path:
            raise RuntimeError("Missing {object_type} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ModuleRemoveObjectEndpoint(
            path=path,
        )
