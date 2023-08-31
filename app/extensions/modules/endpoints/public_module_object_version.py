from typing import List, Type

import pydantic
from fastapi import APIRouter, Depends, HTTPException

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import depends_active_module, depends_module_object_by_uuid_curried
from app.extensions.modules.endpoints.module_object_version import ModuleObjectVersionEndpoint
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class PublicModuleObjectVersionEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        config_object_id: str,
        object_type: str,
        response_model: Model,
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._config_object_id: str = config_object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            module: ModuleTable = Depends(depends_active_module),
            module_object: ModuleObjectsTable = Depends(depends_module_object_by_uuid_curried(self._object_type)),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> self._response_type:
            if module.Current_Status not in ModuleStatusCode.after(ModuleStatusCode.Ontwerp_GS):
                raise HTTPException(
                    status_code=401, detail="module objects lacks the minimum status for unauthenticated view."
                )
            return ModuleObjectVersionEndpoint._handler(
                event_dispatcher, module_object, self._response_type, self._response_model, self._endpoint_id
            )

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=self._response_type,
            summary=f"Get public {self._object_type} revision by uuid from a module",
            description=None,
            tags=[self._object_type],
        )

        return router


class PublicModuleObjectVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "public_module_object_version"

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

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{module_id}" in path:
            raise RuntimeError("Missing {module_id} argument in path")
        if not "{object_uuid}" in path:
            raise RuntimeError("Missing {object_uuid} argument in path")

        return PublicModuleObjectVersionEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            config_object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
        )
