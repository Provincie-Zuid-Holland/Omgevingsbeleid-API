from typing import List, Type

from fastapi import APIRouter, Depends
import pydantic
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, Model, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.werkingsgebieden.db.tables import ObjectWerkingsgebiedenTable


class ListWerkingsgebiedenEndpoint(Endpoint):
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
            lineage_id: int,
            db: Session = Depends(depends_db),
        ) -> List[self._response_type]:
            return self._handler(db, lineage_id)

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[self._response_type],
            summary=f"Get all werkingsgebieden UUIDs of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router

    def _handler(
        self,
        db: Session,
        lineage_id: int,
    ):
        object_code: str = f"{self._object_type}-{lineage_id}"
        stmt = select(ObjectWerkingsgebiedenTable).filter(
            ObjectWerkingsgebiedenTable.Object_Code == object_code
        )
        table_rows = db.scalars(stmt).all()

        response: List[self._response_type] = [
            self._response_type.from_orm(r) for r in table_rows
        ]

        return response


class ListWerkingsgebiedenEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_werkingsgebieden"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        response_model = models_resolver.get("werkingsgebied_short")

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ListWerkingsgebiedenEndpoint(
            converter=converter,
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
            response_model=response_model,
        )
