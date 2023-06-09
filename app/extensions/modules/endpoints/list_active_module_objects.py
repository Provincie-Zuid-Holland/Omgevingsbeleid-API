from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.converter import Converter
from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_static_repository import ObjectStaticRepository
from app.extensions.modules.event.retrieved_module_objects_event import (
    RetrievedModuleObjectsEvent,
)
from app.extensions.modules.models import Module, ActiveModuleObject
from app.extensions.modules.dependencies import (
    depends_module_object_repository,
)
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ListActiveModuleObjectsEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        event_dispatcher: EventDispatcher,
        object_type: str,
        response_model: Model,
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path
        self._converter: Converter = converter
        self._endpoint_id: str = endpoint_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            minimum_status: ModuleStatusCode = ModuleStatusCode.Ontwerp_PS,
            module_object_repository: ModuleObjectRepository = Depends(
                depends_module_object_repository
            ),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> List[ActiveModuleObject]:
            return self._handler(
                lineage_id, minimum_status, module_object_repository, event_dispatcher
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ActiveModuleObject],
            summary=f"List the last modified module object grouped per module ID",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        lineage_id: int,
        minimum_status: ModuleStatusCode,
        module_object_repository: ModuleObjectRepository,
        event_dispatcher: EventDispatcher,
    ):
        code = f"{self._object_type}-{lineage_id}"
        module_objects = module_object_repository.get_latest_per_module(
            code=code, minimum_status=minimum_status, is_active=True
        )
        if len(module_objects) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No active revisions found for lineage {lineage_id}",
            )

        rows: List[ActiveModuleObject] = [
            ActiveModuleObject.from_orm(r) for r in module_objects
        ]
        # Ask extensions for more information
        event: RetrievedModuleObjectsEvent = event_dispatcher.dispatch(
            RetrievedModuleObjectsEvent.create(
                rows,
                self._endpoint_id,
                self._response_model,
            )
        )
        rows = event.payload.rows

        return rows


class ListActiveModuleObjectsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_active_module_objects"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get(resolver_config.get("response_model"))

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ListActiveModuleObjectsEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            event_dispatcher=event_dispatcher,
            path=path,
            object_type=api.object_type,
            response_model=response_model,
        )
