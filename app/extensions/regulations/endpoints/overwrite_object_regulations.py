from typing import List
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.dependencies import depends_db
from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.dependencies import depends_object_static_by_object_type_and_id_curried

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.utils.response import ResponseOK
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.regulations.db.tables import ObjectRegulationsTable
from app.extensions.regulations.permissions import RegulationsPermissions
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
)


class RegulationObjectOverwrite(BaseModel):
    UUID: uuid.UUID

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_code: str,
        overwrite_list: List[RegulationObjectOverwrite],
    ):
        self._db: Session = db
        self._object_code: str = object_code
        self._overwrite_list: List[RegulationObjectOverwrite] = overwrite_list

    def handle(self) -> ResponseOK:
        try:
            self._remove_current_regulations()
            self._create_regulations()
            self._db.commit()

            return ResponseOK(
                message="OK",
            )
        except Exception as e:
            self._db.rollback()
            raise e

    def _remove_current_regulations(self):
        stmt = delete(ObjectRegulationsTable).filter(
            ObjectRegulationsTable.Object_Code == self._object_code
        )
        self._db.execute(stmt)

    def _create_regulations(self):
        if not self._overwrite_list:
            return

        for data in self._overwrite_list:
            object_regulation: ObjectRegulationsTable = ObjectRegulationsTable(
                Object_Code=self._object_code,
                Regulation_UUID=data.UUID,
            )
            self._db.add(object_regulation)


class OverwriteObjectRegulationsEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
    ):
        self._path: str = path
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            overwrite_list: List[RegulationObjectOverwrite],
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    RegulationsPermissions.can_overwrite_object_regulations
                )
            ),
            object_static: ObjectStaticsTable = Depends(
                depends_object_static_by_object_type_and_id_curried(self._object_type)
            ),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_static.Code,
                overwrite_list,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PUT"],
            response_model=ResponseOK,
            summary=f"Overwrite all regulations of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class OverwriteObjectRegulationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "overwrite_object_regulations"

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

        return OverwriteObjectRegulationsEndpoint(
            path=path,
            object_type=api.object_type,
        )
