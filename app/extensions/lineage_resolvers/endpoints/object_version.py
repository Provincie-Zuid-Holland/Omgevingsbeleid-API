from ast import List
from typing import List, Optional, Type
from uuid import UUID

import pydantic
from fastapi import APIRouter, Depends

from app.dynamic.config.models import Api, EndpointConfig, Model
from app.dynamic.converter import Converter
from app.dynamic.db import ObjectsTable
from app.dynamic.dependencies import depends_event_dispatcher, depends_object_repository
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event import RetrievedObjectsEvent
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.repository.object_repository import ObjectRepository


class ObjectVersionEndpoint(Endpoint):
    def __init__(
        self,
        converter: Converter,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
        response_model: Model,
    ):
        self._converter: Converter = converter
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type
        self._response_model: Model = response_model
        self._response_type: Type[pydantic.BaseModel] = response_model.pydantic_model

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_uuid: UUID,
            object_repository: ObjectRepository = Depends(depends_object_repository),
            event_dispatcher: EventDispatcher = Depends(depends_event_dispatcher),
        ) -> self._response_type:
            return self._handler(object_repository, event_dispatcher, object_uuid)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=self._response_type,
            summary=f"Get specific {self._object_type} by uuid",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        object_repository: ObjectRepository,
        event_dispatcher: EventDispatcher,
        object_uuid: UUID,
    ):
        maybe_object: Optional[ObjectsTable] = object_repository.get_by_object_type_and_uuid(
            self._object_type,
            object_uuid,
        )
        if not maybe_object:
            raise ValueError("object_uuid does not exist")

        row: self._response_type = self._response_type.from_orm(maybe_object)
        rows: List[self._response_type] = [row]

        # Ask extensions for more information
        rows = self._run_events([maybe_object], event_dispatcher)

        return rows[0]

    def _run_events(self, table_rows: List[ObjectsTable], event_dispatcher: EventDispatcher):
        """
        Ask extensions for more information.
        """
        event: RetrievedObjectsEvent = event_dispatcher.dispatch(
            RetrievedObjectsEvent.create(
                table_rows,
                self._endpoint_id,
                self._response_model,
            )
        )
        return event.payload.rows


class ObjectVersionEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "object_version"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get(resolver_config.get("response_model"))

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{object_uuid}" in path:
            raise RuntimeError("Missing {object_uuid} argument in path")

        return ObjectVersionEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
        )
