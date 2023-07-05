import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, aliased, joinedload, load_only

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.modules.models import Module
from app.extensions.modules.models.models import ModuleStatus
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class ObjectStaticShort(BaseModel):
    Owner_1_UUID: Optional[uuid.UUID]
    Owner_2_UUID: Optional[uuid.UUID]

    class Config:
        orm_mode = True


class ModuleObjectContextShort(BaseModel):
    Action: str
    Original_Adjust_On: Optional[uuid.UUID]

    class Config:
        orm_mode = True


class ModuleObjectShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str
    UUID: uuid.UUID

    Modified_Date: datetime
    Title: str

    ObjectStatics: Optional[ObjectStaticShort]
    ModuleObjectContext: Optional[ModuleObjectContextShort]

    class Config:
        orm_mode = True


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
        subq = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .filter(ModuleObjectsTable.Module_ID == self._module.Module_ID)
            .subquery()
        )

        aliased_subq = aliased(ModuleObjectsTable, subq)
        stmt = (
            select(aliased_subq)
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
            .options(
                load_only(
                    aliased_subq.Module_ID,
                    aliased_subq.Object_Type,
                    aliased_subq.Object_ID,
                    aliased_subq.Code,
                    aliased_subq.UUID,
                    aliased_subq.Modified_Date,
                    aliased_subq.Title,
                    aliased_subq.Deleted,
                ),
                joinedload(aliased_subq.ModuleObjectContext),
                joinedload(aliased_subq.ObjectStatics),
            )
        )

        rows: List[ModuleObjectsTable] = self._db.execute(stmt).scalars().all()
        objects: List[ModuleObjectShort] = [ModuleObjectShort.from_orm(r) for r in rows]
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
