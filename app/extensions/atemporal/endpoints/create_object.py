from typing import Type
from datetime import datetime
import uuid

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, insert, String
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.converter import Converter
from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.atemporal.permissions import AtemporalPermissions
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import (
    depends_current_active_user_with_permission_curried,
)


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_id: str,
        object_type: str,
        response_type: Type[BaseModel],
        user: UsersTable,
        object_in: dict,
    ):
        self._db: Session = db
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._response_type: Type[BaseModel] = response_type
        self._user: UsersTable = user
        self._object_in: dict = object_in
        self._timepoint: datetime = datetime.now()

    def handle(self) -> Type[BaseModel]:
        static_fields: dict = {}
        if "ObjectStatics" in self._object_in:
            static_fields = self._object_in["ObjectStatics"]
            del self._object_in["ObjectStatics"]

        try:
            object_static: ObjectStaticsTable = self._create_new_object_static(
                static_fields
            )
            created_object: Type[BaseModel] = self._create_object(object_static)

            self._db.flush()
            self._db.commit()

            return created_object
        except Exception:
            self._db.rollback
            raise

    def _create_new_object_static(self, static_fields: dict) -> ObjectStaticsTable:
        generate_id_subq = (
            select(func.coalesce(func.max(ObjectStaticsTable.Object_ID), 0) + 1)
            .select_from(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == self._object_type)
            .scalar_subquery()
        )

        stmt = (
            insert(ObjectStaticsTable)
            .values(
                Object_Type=self._object_type,
                Object_ID=generate_id_subq,
                Code=(self._object_type + "-" + func.cast(generate_id_subq, String)),
                Cached_Title=self._object_in["Title"],
                # Unpack object_in static fields
                **(static_fields),
            )
            .returning(ObjectStaticsTable)
        )

        response: ObjectStaticsTable = self._db.execute(stmt).scalars().first()
        return response

    def _create_object(self, object_static: ObjectStaticsTable):
        new_object: ObjectsTable = ObjectsTable(
            Object_Type=object_static.Object_Type,
            Object_ID=object_static.Object_ID,
            Code=object_static.Code,
            UUID=uuid.uuid4(),
            Created_Date=self._timepoint,
            Modified_Date=self._timepoint,
            Created_By_UUID=self._user.UUID,
            Modified_By_UUID=self._user.UUID,
            Start_Validity=self._timepoint,
            # Unpack object_in fields
            **(self._object_in),
        )
        self._db.add(new_object)
        return new_object


class CreateObjectEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_id: str,
        object_type: str,
        request_type: Type[BaseModel],
        response_type: Type[BaseModel],
    ):
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._request_type: Type[BaseModel] = request_type
        self._response_type: Type[BaseModel] = response_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_in: self._request_type,
            db: Session = Depends(depends_db),
            user: UsersTable = Depends(
                depends_current_active_user_with_permission_curried(
                    AtemporalPermissions.atemporal_can_create_object,
                ),
            ),
        ) -> self._response_type:
            handler: EndpointHandler = EndpointHandler(
                db,
                self._object_id,
                self._object_type,
                self._response_type,
                user,
                object_in.dict(exclude_none=True),
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=self._response_type,
            summary=f"Add new object",
            description=None,
            tags=[self._object_type],
        )

        return router


class CreateObjectEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "atemporal_create_object"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        request_model = models_resolver.get(resolver_config.get("request_model"))
        request_type: Type[BaseModel] = request_model.pydantic_model

        response_model = models_resolver.get(resolver_config.get("response_model"))
        response_type: Type[BaseModel] = response_model.pydantic_model

        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return CreateObjectEndpoint(
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            request_type=request_type,
            response_type=response_type,
        )
