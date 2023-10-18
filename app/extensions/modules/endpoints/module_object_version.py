from typing import List, Optional, Sequence, Type

import pydantic
from fastapi import APIRouter, Depends, HTTPException, params

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.converter import Converter
from app.dynamic.dependencies import depends_event_dispatcher
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.dependencies import depends_active_module, depends_module_object_by_uuid_curried
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.modules.models.models import ModuleStatusCode
from app.extensions.users.dependencies import depends_current_active_user, depends_current_user, optional_user
from app.extensions.users.db.tables import UsersTable


class ModuleObjectVersionEndpoint(Endpoint):
    def __init__(
        self,
        endpoint_id: str,
        path: str,
        config_object_id: str,
        object_type: str,
        response_model: Model,
        require_auth: bool,
        minimum: Optional[ModuleStatusCode],
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._config_object_id: str = config_object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model
        self._require_auth: bool = require_auth
        self._minimum_status: Optional[ModuleStatusCode] = minimum

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            user: UsersTable = Depends(optional_user),
            module: ModuleTable = Depends(depends_active_module),
            module_object: ModuleObjectsTable = Depends(depends_module_object_by_uuid_curried(self._object_type)),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> self._response_type:
            if not user and self._minimum_status:
                if module.Current_Status not in ModuleStatusCode.after(self._minimum_status):
                    raise HTTPException(status_code=401, detail="module objects lacks the minimum status for view.")

            return self._handler(event_dispatcher, module_object)

        dependencies: Sequence[params.Depends] = []
        if self._require_auth:
            dependencies.append(Depends(depends_current_active_user))

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=self._response_type,
            summary=f"Get specific {self._object_type} by uuid in a module",
            description=None,
            tags=[self._object_type],
            dependencies=dependencies,
        )

        return router

    def _handler(
        self,
        event_dispatcher: EventDispatcher,
        module_object: ModuleObjectsTable,
    ):
        context: ModuleObjectContextTable = module_object.ModuleObjectContext
        if context.Hidden:
            raise HTTPException(status_code=404, detail="Module Object Context is verwijderd")

        row: self._response_type = self._response_type.from_orm(module_object)
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


class ModuleObjectVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_object_version"

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

        require_auth: bool = resolver_config.get("require_auth", True)

        minimum_status: Optional[ModuleStatusCode] = None
        requested_minimum_status: Optional[str] = resolver_config.get("minimum_status", None)
        if requested_minimum_status:
            try:
                minimum_status = ModuleStatusCode(requested_minimum_status)
            except ValueError:
                raise RuntimeError("Invalid module status code: {requested_minimum_status}")

        return ModuleObjectVersionEndpoint(
            endpoint_id=self.get_id(),
            path=path,
            config_object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
            require_auth=require_auth,
            minimum=minimum_status,
        )
