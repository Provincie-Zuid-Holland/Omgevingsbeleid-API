from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.dependencies import depends_module_object_repository
from app.extensions.modules.models.models import ActiveModuleObject, ModuleShort, ModuleStatusCode
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ActiveModuleObjectWrapper(BaseModel):
    Module: ModuleShort
    Module_Object: ActiveModuleObject


class ListActiveModuleObjectsEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
        response_model: Model,
    ):
        self._path: str = path
        self._object_type: str = object_type
        self._response_model: Model = response_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            minimum_status: ModuleStatusCode = ModuleStatusCode.Ontwerp_PS,
            module_object_repository: ModuleObjectRepository = Depends(depends_module_object_repository),
            user: UsersTable = Depends(depends_current_active_user),
        ) -> List[ActiveModuleObjectWrapper]:
            return self._handler(lineage_id, minimum_status, module_object_repository)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ActiveModuleObjectWrapper],
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
    ):
        code = f"{self._object_type}-{lineage_id}"
        items = module_object_repository.get_latest_per_module(code=code, minimum_status=minimum_status, is_active=True)

        rows: List[ActiveModuleObjectWrapper] = []
        for module_object, module in items:
            rows.append(
                ActiveModuleObjectWrapper(
                    Module=ModuleShort.from_orm(module), Module_Object=ActiveModuleObject.from_orm(module_object)
                )
            )

        return rows


class ListActiveModuleObjectsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_active_module_objects"

    def generate_endpoint(
        self,
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
            path=path,
            object_type=api.object_type,
            response_model=response_model,
        )
