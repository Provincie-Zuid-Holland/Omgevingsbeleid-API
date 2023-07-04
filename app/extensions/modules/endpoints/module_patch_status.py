from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.modules.db.tables import ModuleStatusHistoryTable, ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_and_activated_module,
)
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models.models import ModulePatchStatus
from app.extensions.modules.permissions import (
    ModulesPermissions,
    guard_module_is_locked,
    guard_valid_user,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_permission_service,
)
from app.extensions.users.permission_service import PermissionService


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        event_dispatcher: EventDispatcher,
        permission_service: PermissionService,
        user: UsersTable,
        module: ModuleTable,
        object_in: ModulePatchStatus,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._permission_service: PermissionService = permission_service
        self._db: Session = db
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._object_in: ModulePatchStatus = object_in

    def handle(self) -> ResponseOK:
        guard_valid_user(
            self._permission_service,
            ModulesPermissions.can_patch_module_status,
            self._user,
            self._module,
        )
        guard_module_is_locked(self._module)

        status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
            Module_ID=self._module.Module_ID,
            Status=self._object_in.Status,
            Created_Date=datetime.utcnow(),
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(status)
        self._db.flush()
        self._db.commit()

        self._dispatch_status_changed_event(status)

        return ResponseOK(
            message="OK",
        )

    def _dispatch_status_changed_event(self, new_status: ModuleStatusHistoryTable):
        self._event_dispatcher.dispatch(
            ModuleStatusChangedEvent.create(
                self._module,
                new_status,
            )
        )


class ModulePatchStatusEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModulePatchStatus,
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_and_activated_module),
            db: Session = Depends(depends_db),
            permission_service: PermissionService = Depends(depends_permission_service),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                event_dispatcher,
                permission_service,
                user,
                module,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PATCH"],
            response_model=ResponseOK,
            summary=f"Patch the status of the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModulePatchStatusEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_patch_status"

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

        return ModulePatchStatusEndpoint(path=path)
