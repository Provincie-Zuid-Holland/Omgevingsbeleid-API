from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.tables import ModuleTable, ModuleObjectContextTable
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.modules.models import Module
from app.extensions.modules.models.models import ModuleObjectShort, ModuleStatus
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ModuleOverview(BaseModel):
    Module: Module
    StatusHistory: List[ModuleStatus]
    Objects: List[ModuleObjectShort]


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        module: ModuleTable,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._module: ModuleTable = module

    def handle(self) -> ModuleOverview:
        objects: List[ModuleObjectShort] = self._get_objects()

        response: ModuleOverview = ModuleOverview(
            Module=self._module,
            StatusHistory=self._module.status_history,
            Objects=objects,
        )
        return response

    def _get_objects(self) -> List[ModuleObjectShort]:
        # Get the newest version of each Code
        subq = (
            select(
                ModuleObjectsTable.Module_ID,
                ModuleObjectsTable.Object_Type,
                ModuleObjectsTable.Object_ID,
                ModuleObjectsTable.Code,
                ModuleObjectsTable.UUID,
                ModuleObjectsTable.Modified_Date,
                ModuleObjectsTable.Title,
                ModuleObjectsTable.Deleted,
                ObjectStaticsTable.Owner_1_UUID,
                ObjectStaticsTable.Owner_2_UUID,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ObjectStaticsTable)
            .filter(ModuleObjectsTable.Module_ID == self._module.Module_ID)
            .subquery()
        )

        stmt = (
            select(
                subq,
                ModuleObjectContextTable.Action,
                ModuleObjectContextTable.Original_Adjust_On,
            )
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
            .join(ModuleObjectContextTable)
        )

        rows = self._db.execute(stmt).all()
        objects: List[ModuleObjectShort] = [
            ModuleObjectShort.parse_obj(r._asdict()) for r in rows
        ]
        return objects


class ModuleOverviewEndpoint(Endpoint):
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
        ) -> ModuleOverview:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                module,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=ModuleOverview,
            summary=f"Get overview of a module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleOverviewEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_overview"

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

        return ModuleOverviewEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
        )
