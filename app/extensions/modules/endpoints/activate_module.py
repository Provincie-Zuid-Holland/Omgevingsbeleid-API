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
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.modules.event.module_status_changed_event import (
    ModuleStatusChangedEvent,
)
from app.extensions.modules.models import Module
from app.extensions.modules.models.models import AllModuleStatusCode
from app.extensions.modules.permissions import (
    guard_module_not_activated,
    guard_user_is_module_manager,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        event_dispatcher: EventDispatcher,
        user: UsersTable,
        module: Module,
    ):
        self._db: Session = db
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._user: UsersTable = user
        self._module: ModuleTable = module
        self._timepoint: datetime = datetime.now()

    def handle(self) -> ResponseOK:
        guard_user_is_module_manager(self._user, self._module)
        guard_module_not_activated(self._module)

        self._activate_module()
        self._patch_status()

        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )

    def _activate_module(self):
        self._module.Activated = 1
        self._module.Modified_By_UUID = self._user.UUID
        self._module.Modified_Date = self._timepoint

        self._db.add(self._module)

    def _patch_status(self) -> ModuleStatusHistoryTable:
        status: ModuleStatusHistoryTable = ModuleStatusHistoryTable(
            Module_ID=self._module.Module_ID,
            Status=AllModuleStatusCode.Ontwerp_GS_Concept,
            Created_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
        )
        self._db.add(status)
        return status

    def _dispatch_status_changed_event(self, new_status: ModuleStatusHistoryTable):
        self._event_dispatcher.dispatch(
            ModuleStatusChangedEvent.create(
                self._module,
                new_status,
            )
        )


class ActivateModuleEndpoint(Endpoint):
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        path: str,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                event_dispatcher,
                user,
                module,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Activate a module",
            description=None,
            tags=["Modules"],
        )

        return router


class ActivateModuleEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "activate_module"

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

        return ActivateModuleEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
