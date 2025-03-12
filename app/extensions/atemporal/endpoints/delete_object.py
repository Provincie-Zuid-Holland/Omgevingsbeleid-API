import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.dynamic.dependencies import depends_object_repository, depends_object_static_by_object_type_and_id_curried
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
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
    ):
        self._db: Session = db
        self._object_repository: ObjectRepository = object_repository
        self._permission_service: PermissionService = permission_service
        self._user: UsersTable = user
        self._object_static: ModuleObjectContextTable = object_static
        self._timepoint: datetime = datetime.now(timezone.utc)

    def handle(self) -> ResponseOK:
        self._permission_service.guard_valid_user(
            AtemporalPermissions.atemporal_can_delete_object,
            self._user,
        )

        maybe_object: Optional[ObjectsTable] = self._object_repository.get_latest_by_id(
            self._object_static.Object_Type,
            self._object_static.Object_ID,
        )
        if not maybe_object:
            raise HTTPException(404, "Object not found")
        if maybe_object.End_Validity is not None and maybe_object.End_Validity < self._timepoint:
            raise HTTPException(400, "Object is already deleted")

        log_before: str = json.dumps(maybe_object.to_dict())

        maybe_object.End_Validity = self._timepoint
        maybe_object.Modified_By_UUID = self._user.UUID
        maybe_object.Modified_Date = self._timepoint

        self._db.add(maybe_object)

        change_log: ChangeLogTable = ChangeLogTable(
            Object_Type=self._object_static.Object_Type,
            Object_ID=self._object_static.Object_ID,
            Created_Date=datetime.now(timezone.utc),
            Created_By_UUID=self._user.UUID,
            Action_Type="atemporal_edit_object",
            Before=log_before,
            After=json.dumps(maybe_object.to_dict()),
        )
        self._db.add(change_log)

        self._db.flush()
        self._db.commit()

        return ResponseOK(
            message="OK",
        )


class DeleteObjectEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
    ):
        self._path: str = path
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
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
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["DELETE"],
            response_model=ResponseOK,
            summary=f"Delete atemporal object",
            description=None,
            tags=[self._object_type],
        )

        return router


class DeleteObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "atemporal_delete_object"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return DeleteObjectEndpoint(
            path=path,
            object_type=api.object_type,
        )
