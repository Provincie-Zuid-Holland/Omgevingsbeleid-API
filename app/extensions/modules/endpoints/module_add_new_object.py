from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, insert, String
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.converter import Converter
from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable, ModuleObjectContextTable
from app.extensions.modules.dependencies import depends_active_module
from app.extensions.modules.permissions import ModulesPermissions
from app.extensions.users.db.tables import GebruikersTable
from app.extensions.users.dependencies import (
    depends_current_active_user,
    depends_permission_service,
)
from app.extensions.users.permission_service import PermissionService


class ModuleAddNewObject(BaseModel):
    Object_Type: str
    Title: str = Field(..., min_length=3)
    Owner_1_UUID: uuid.UUID
    Owner_2_UUID: Optional[uuid.UUID] = Field(None, nullable=True)
    Client_1_UUID: Optional[uuid.UUID] = Field(None, nullable=True)

    Explanation: str
    Conclusion: str

    @validator("Owner_2_UUID")
    def duplicate_owner(cls, v, values):
        if v is None:
            return v
        if not "Owner_1_UUID" in values:
            return v
        if v == values["Owner_1_UUID"]:
            raise ValueError("Duplicate owner")
        return v


class NewObjectStaticResponse(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str

    class Config:
        orm_mode = True


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        allowed_object_types: List[str],
        permission_service: PermissionService,
        user: GebruikersTable,
        module: ModuleTable,
        object_in: ModuleAddNewObject,
    ):
        self._db: Session = db
        self._allowed_object_types: List[str] = allowed_object_types
        self._permission_service: PermissionService = permission_service
        self._user: GebruikersTable = user
        self._module: ModuleTable = module
        self._object_in: ModuleAddNewObject = object_in
        self._timepoint: datetime = datetime.now()

    def handle(self) -> NewObjectStaticResponse:
        self._guard_valid_user()

        if self._object_in.Object_Type not in self._allowed_object_types:
            raise HTTPException(
                400,
                f"Invalid Object_Type, accepted object_type are: {self._allowed_object_types}",
            )

        try:
            object_static: ObjectStaticsTable = self._create_new_object_static()
            self._create_object_context(object_static)
            self._create_object(object_static)

            self._db.flush()
            self._db.commit()

            response: NewObjectStaticResponse = NewObjectStaticResponse.from_orm(
                object_static
            )
            return response
        except Exception as e:
            self._db.rollback
            raise HTTPException(500, "Could not add object to the module")

    def _create_new_object_static(self) -> ObjectStaticsTable:
        generate_id_subq = (
            select(func.coalesce(func.max(ObjectStaticsTable.Object_ID), 0) + 1)
            .select_from(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == self._object_in.Object_Type)
            .scalar_subquery()
        )

        stmt = (
            insert(ObjectStaticsTable)
            .values(
                Object_Type=self._object_in.Object_Type,
                Object_ID=generate_id_subq,
                Code=(
                    self._object_in.Object_Type
                    + "-"
                    + func.cast(generate_id_subq, String)
                ),
                # @todo: should be generated based on columns.statics
                Owner_1_UUID=self._object_in.Owner_1_UUID,
                Owner_2_UUID=self._object_in.Owner_2_UUID,
                Client_1_UUID=self._object_in.Client_1_UUID,
            )
            .returning(ObjectStaticsTable)
        )

        response: ObjectStaticsTable = self._db.execute(stmt).scalars().first()
        return response

    def _create_object_context(self, object_static: ObjectStaticsTable):
        object_context: ModuleObjectContextTable = ModuleObjectContextTable(
            Module_ID=self._module.Module_ID,
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
            Original_Adjust_On=None,
            Action="Create",
            Explanation=self._object_in.Explanation,
            Conclusion=self._object_in.Conclusion,
        )
        self._db.add(object_context)

    def _create_object(self, object_static: ObjectStaticsTable):
        module_object: ModuleObjectsTable = ModuleObjectsTable(
            Module_ID=self._module.Module_ID,
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            UUID=uuid.uuid4(),
            Title=self._object_in.Title,
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
        )
        self._db.add(module_object)

    def _guard_valid_user(self):
        if self._module.is_manager(self._user.UUID):
            return

        if not self._permission_service.has_permission(
            ModulesPermissions.can_add_new_object_to_module, self._user
        ):
            raise HTTPException(status_code=401, detail="Invalid user role")


class ModuleAddNewObjectEndpoint(Endpoint):
    def __init__(
        self,
        allowed_object_types: List[str],
        path: str,
    ):
        self._allowed_object_types: List[str] = allowed_object_types
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: ModuleAddNewObject,
            user: GebruikersTable = Depends(depends_current_active_user),
            module: ModuleTable = Depends(depends_active_module),
            db: Session = Depends(depends_db),
            permission_service: PermissionService = Depends(depends_permission_service),
        ) -> NewObjectStaticResponse:
            handler: EndpointHandler = EndpointHandler(
                db,
                self._allowed_object_types,
                permission_service,
                user,
                module,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=NewObjectStaticResponse,
            summary=f"Add new object to the module",
            description=None,
            tags=["Modules"],
        )

        return router


class ModuleAddNewObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "module_add_new_object"

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

        allowed_object_types: List[str] = resolver_config.get(
            "allowed_object_types", []
        )
        if not allowed_object_types:
            raise RuntimeError("Missing allowed_object_types")

        return ModuleAddNewObjectEndpoint(
            allowed_object_types=allowed_object_types,
            path=path,
        )
