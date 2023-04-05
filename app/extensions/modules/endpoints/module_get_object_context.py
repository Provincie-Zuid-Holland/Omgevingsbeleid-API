from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleObjectContextTable
from app.extensions.modules.dependencies import (
    depends_active_module_object_context,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user
from app.extensions.users.model import UserShort


class ModuleObjectContext(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str

    Created_Date: datetime
    Modified_Date: datetime

    Action: str
    Explanation: str
    Conclusion: str

    Original_Adjust_On: Optional[uuid.UUID]

    Created_By: Optional[UserShort]
    Modified_By: Optional[UserShort]

    class Config:
        orm_mode = True


class ModuleGetObjectContextEndpoint(Endpoint):
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
            object_context_table: ModuleObjectContextTable = Depends(
                depends_active_module_object_context
            ),
        ) -> ModuleObjectContext:
            response: ModuleObjectContext = ModuleObjectContext.from_orm(object_context_table)
            return response

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=ModuleObjectContext,
            summary=f"Get context of object in the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleGetObjectContextEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_get_object_context"

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

        return ModuleGetObjectContextEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
