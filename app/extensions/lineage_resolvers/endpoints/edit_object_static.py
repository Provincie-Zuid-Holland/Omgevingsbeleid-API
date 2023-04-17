from typing import Optional, Type

from fastapi import APIRouter, Depends, HTTPException
import pydantic
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectStaticsTable
from app.dynamic.dependencies import depends_object_static_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_static_repository import ObjectStaticRepository
from app.dynamic.utils.response import ResponseOK
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        converter: Converter,
        object_config_id: str,
        object_type: str,
        db: Session,
        repository: ObjectStaticRepository,
        user: UsersTable,
        changes: dict,
        lineage_id: int,
    ):
        self._converter: Converter = converter
        self._object_config_id: str = object_config_id
        self._object_type: str = object_type

        self._db: Session = db
        self._repository: ObjectStaticRepository = repository

        self._user: UsersTable = user
        self._changes: dict = changes
        self._lineage_id: int = lineage_id

    def handle(self):
        if not self._changes:
            raise HTTPException(400, "Nothing to update")

        object_static: Optional[
            ObjectStaticsTable
        ] = self._repository.get_by_object_type_and_id(
            self._object_type,
            self._lineage_id,
        )
        if not object_static:
            raise ValueError(f"lineage_id does not exist")

        for key, value in self._changes.items():
            setattr(object_static, key, value)

        self._db.flush()
        self._db.commit()

        return ResponseOK(message="OK")


class EditObjectStaticEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        object_config_id: str,
        object_type: str,
        path: str,
        request_type: Type[pydantic.BaseModel],
    ):
        self._converter: Converter = converter
        self._object_config_id: str = object_config_id
        self._object_type: str = object_type
        self._path: str = path
        self._request_type: Type[pydantic.BaseModel] = request_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            object_in: self._request_type,
            user: UsersTable = Depends(depends_current_active_user),
            db: Session = Depends(depends_db),
            repository: ObjectStaticRepository = Depends(
                depends_object_static_repository
            ),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                self._converter,
                self._object_config_id,
                self._object_type,
                db,
                repository,
                user,
                object_in.dict(exclude_none=True),
                lineage_id,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit static data of an object",
            description=None,
            tags=[self._object_type],
        )

        return router


class EditObjectStaticEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_object_static"

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
        request_type: Type[pydantic.BaseModel] = request_model.pydantic_model

        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return EditObjectStaticEndpoint(
            converter=converter,
            object_config_id=api.id,
            object_type=api.object_type,
            path=path,
            request_type=request_type,
        )
