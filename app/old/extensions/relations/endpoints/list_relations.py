from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core_old.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.extensions.relations.db.tables import RelationsTable
from app.extensions.relations.models.models import ReadRelation


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        object_code: str,
    ):
        self._db: Session = db
        self._object_code: str = object_code

    def handle(self) -> List[ReadRelation]:
        stmt = (
            select(RelationsTable)
            .filter(
                or_(
                    RelationsTable.From_Code == self._object_code,
                    RelationsTable.To_Code == self._object_code,
                )
            )
            .options(
                selectinload(RelationsTable.FromObjectStatics),
                selectinload(RelationsTable.ToObjectStatics),
            )
        )
        table_rows: List[RelationsTable] = self._db.scalars(stmt).all()
        response: List[RelationsTable] = self._format_rows(table_rows)
        return response

    def _format_rows(self, table_rows: List[RelationsTable]) -> List[ReadRelation]:
        result: List[ReadRelation] = []

        for row in table_rows:
            # Need to determine which the relation is based on my_code
            title: str = row.FromObjectStatics.Cached_Title
            relation_code: str = row.From_Code
            if relation_code == self._object_code:
                relation_code = row.To_Code
                title = row.ToObjectStatics.Cached_Title

            # Decode the code into object_type and ID, as that is easier to use for the client
            relation_object_type, relation_id = relation_code.split("-", 1)

            response_model: ReadRelation = ReadRelation(
                Object_ID=relation_id,
                Object_Type=relation_object_type,
                Description=row.Description,
                Title=title,
            )
            result.append(response_model)

        return result


class ListRelationsEndpoint(Endpoint):
    def __init__(
        self,
        endpoint_id: str,
        path: str,
        object_id: str,
        object_type: str,
    ):
        self._endpoint_id: str = endpoint_id
        self._path: str = path
        self._object_id: str = object_id
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            db: Session = Depends(depends_db),
        ) -> List[ReadRelation]:
            handler: EndpointHandler = EndpointHandler(
                db,
                f"{self._object_type}-{lineage_id}",
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=List[ReadRelation],
            summary=f"Get all relation codes of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class ListRelationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "list_relations"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        return ListRelationsEndpoint(
            endpoint_id=self.get_id(),
            path=path,
            object_id=api.id,
            object_type=api.object_type,
        )
