from typing import List, Optional, Type

import pydantic
from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import (
    depends_active_module,
    depends_active_module_object_context_curried,
    depends_module_object_repository,
)
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleObjectLatestEndpoint(Endpoint):
    def __init__(
        self,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
        response_model: Model,
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            user: UsersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            module_object_context=Depends(depends_active_module_object_context_curried(self._object_type)),
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> self._response_type:
            return self._handler(module_object_repository, event_dispatcher, module, lineage_id)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=self._response_type,
            summary=f"Get latest lineage record for {self._object_type} by their lineage id in a module",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        module_object_repository: ModuleObjectRepository,
        event_dispatcher: EventDispatcher,
        module: ModuleTable,
        lineage_id: int,
    ):
        module_object: Optional[ModuleObjectsTable] = module_object_repository.get_latest_by_id(
            module.Module_ID,
            self._object_type,
            lineage_id,
        )
        if not module_object:
            raise ValueError("lineage_id does not exist")

        row: self._response_type = self._response_type.model_validate(module_object)
        rows: List[self._response_type] = [row]

        # Ask extensions for more information
        event: RetrievedModuleObjectsEvent = event_dispatcher.dispatch(
            RetrievedModuleObjectsEvent.create(
                rows,
                self._endpoint_id,
                self._response_model,
            )
        )
        rows = event.payload.rows

        return rows[0]


class ModuleObjectLatestEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_object_latest"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get(resolver_config.get("response_model"))

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ModuleObjectLatestEndpoint(
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
        )
