import json
from datetime import datetime
from typing import Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.dynamic.dependencies import depends_object_repository, depends_object_static_by_object_type_and_id_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository
from app.dynamic.utils.response import ResponseOK
from app.extensions.atemporal.permissions import AtemporalPermissions
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.modules.db.tables import ModuleObjectContextTable
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user, depends_permission_service
from app.extensions.users.permission_service import PermissionService


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_repository: ObjectRepository,
        permission_service: PermissionService,
        user: UsersTable,
        object_static: ObjectStaticsTable,
        object_in: Type[BaseModel],
    ):
        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository
        self._permission_service: PermissionService = permission_service
        self._user: UsersTable = user
        self._object_static: ModuleObjectContextTable = object_static
        self._object_in: Type[BaseModel] = object_in

    def handle(self) -> ResponseOK:
        self._permission_service.guard_valid_user(
            AtemporalPermissions.atemporal_can_edit_object,
            self._user,
        )

        maybe_object: Optional[ObjectsTable] = self._object_repository.get_latest_by_id(
            self._object_static.Object_Type,
            self._object_static.Object_ID,
        )
        if not maybe_object:
            raise HTTPException(404, "Object not found")

        changes: dict = self._object_in.dict(exclude_unset=True)
        if not changes:
            raise HTTPException(400, "Nothing to update")

        log_before: str = json.dumps(maybe_object.to_dict())

        for key, value in changes.items():
            setattr(maybe_object, key, value)

        maybe_object.Modified_By_UUID = self._user.UUID
        maybe_object.Modified_Date = datetime.utcnow()

        if "Title" in changes:
            self._object_static.Cached_Title = changes["Title"]
            self._db.add(self._object_static)

        self._db.add(maybe_object)

        change_log: ChangeLogTable = ChangeLogTable(
            Object_Type=self._object_static.Object_Type,
            Object_ID=self._object_static.Object_ID,
            Created_Date=datetime.utcnow(),
            Created_By_UUID=self._user.UUID,
            Action_Type="atemporal_edit_object",
            Action_Data=self._object_in.json(),
            Before=log_before,
            After=json.dumps(maybe_object.to_dict()),
        )
        self._db.add(change_log)

        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )


class EditObjectEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
        request_type: Type[BaseModel],
    ):
        self._path: str = path
        self._object_type: str = object_type
        self._request_type: Type[BaseModel] = request_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: self._request_type,
            user: UsersTable = Depends(depends_current_active_user),
            object_static: ObjectStaticsTable = Depends(
                depends_object_static_by_object_type_and_id_curried(self._object_type),
            ),
            object_repository: ObjectRepository = Depends(depends_object_repository),
            db: Session = Depends(depends_db),
            permission_service: PermissionService = Depends(depends_permission_service),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_repository,
                permission_service,
                user,
                object_static,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit atemporal object",
            description=None,
            tags=[self._object_type],
        )

        return router


class EditObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "atemporal_edit_object"

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
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        request_model = models_resolver.get(resolver_config.get("request_model"))
        request_type: Type[BaseModel] = request_model.pydantic_model

        return EditObjectEndpoint(
            path=path,
            object_type=api.object_type,
            request_type=request_type,
        )
