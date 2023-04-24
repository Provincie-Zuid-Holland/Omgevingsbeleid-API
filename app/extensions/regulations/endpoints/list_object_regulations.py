from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.dependencies import depends_object_static_by_object_type_and_id_curried
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.regulations.db.tables import (
    ObjectRegulationsTable,
    RegulationsTable,
)
from app.extensions.regulations.models.models import Regulation


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_code: str,
    ):
        self._db: Session = db
        self._object_code: str = object_code

    def handle(self) -> List[Regulation]:
        stmt = (
            select(RegulationsTable)
            .select_from(ObjectRegulationsTable)
            .join(RegulationsTable)
            .filter(
                ObjectRegulationsTable.Object_Code == self._object_code,
            )
        )
        table_rows: List[RegulationsTable] = self._db.scalars(stmt).all()
        response: List[Regulation] = [Regulation.from_orm(r) for r in table_rows]
        return response


class ListObjectRegulationsEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
    ):
        self._path: str = path
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            object_static: ObjectStaticsTable = Depends(
                depends_object_static_by_object_type_and_id_curried(self._object_type)
            ),
            db: Session = Depends(depends_db),
        ) -> List[Regulation]:
            handler: EndpointHandler = EndpointHandler(
                db,
                object_static.Code,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[Regulation],
            summary=f"Get all regulations attached to the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class ListObjectRegulationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_object_regulations"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ListObjectRegulationsEndpoint(
            path=path,
            object_type=api.object_type,
        )
