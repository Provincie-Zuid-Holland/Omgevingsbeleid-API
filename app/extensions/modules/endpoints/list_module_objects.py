from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dynamic.config.models import EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.dependencies import depends_module_object_repository
from app.extensions.modules.endpoints.module_overview import ModuleObjectShort
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.modules.models.models import ModuleObjectActionFilter, ModuleStatusCode
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ListModuleObjectsEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        event_dispatcher: EventDispatcher,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path = path
        self._endpoint_id = endpoint_id
        self._converter: Converter = converter

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_type: Optional[str] = None,
            owner_uuid: Optional[UUID] = None,
            minimum_status: Optional[ModuleStatusCode] = None,
            action: Optional[ModuleObjectActionFilter] = None,
            only_active_modules: bool = True,
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> List[ModuleObjectShort]:
            return self._handler(
                module_object_repository=module_object_repository,
                event_dispatcher=event_dispatcher,
                minimum_status=minimum_status,
                owner_uuid=owner_uuid,
                object_type=object_type,
                only_active_modules=only_active_modules,
                action=action,
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ModuleObjectShort],
            summary="List latest module objects filtered by e.g. owner uuid, object type or minimum status",
            description=None,
            tags=["Modules"],
        )

        return router

    def _handler(
        self,
        module_object_repository: ModuleObjectRepository,
        event_dispatcher: EventDispatcher,
        minimum_status: Optional[ModuleStatusCode],
        owner_uuid: Optional[UUID],
        object_type: Optional[str],
        only_active_modules: bool,
        action: Optional[ModuleObjectActionFilter] = None,
    ):
        module_objects = module_object_repository.get_all_latest(
            only_active_modules=only_active_modules,
            minimum_status=minimum_status,
            owner_uuid=owner_uuid,
            object_type=object_type,
            action=action,
        )

        rows: List[ModuleObjectShort] = [ModuleObjectShort.from_orm(r) for r in module_objects]

        # Ask extensions for more information
        event: RetrievedModuleObjectsEvent = event_dispatcher.dispatch(
            RetrievedModuleObjectsEvent.create(
                rows,
                self._endpoint_id,
                ModuleObjectShort,
            )
        )
        rows = event.payload.rows

        return rows


class ListModuleObjectsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_module_objects"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return ListModuleObjectsEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            event_dispatcher=event_dispatcher,
            path=path,
        )
