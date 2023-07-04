from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select, func, or_
from sqlalchemy.orm import Session, aliased, load_only

from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.graph.models.graph import (
    GraphEdge,
    GraphEdgeType,
    GraphResponse,
    GraphVertice,
)
from app.extensions.relations.db.tables import RelationsTable


class EndpointHandler:
    def __init__(
        self,
        db: Session,
    ):
        self._db: Session = db

    def handle(self) -> GraphResponse:
        vertices: List[GraphVertice] = self._get_all_valid_objects_as_vertices()
        edges: List[GraphEdge] = self._get_all_edges()

        return GraphResponse(
            Vertices=vertices,
            Edges=edges,
        )

    def _get_all_edges(self) -> List[GraphEdge]:
        relations: List[GraphEdge] = self._get_all_relations()
        acknowledged_relations: List[
            GraphEdge
        ] = self._get_valid_acknowledged_relations()

        return relations + acknowledged_relations

    def _get_all_relations(self) -> List[GraphEdge]:
        stmt = select(RelationsTable)
        rows: List[RelationsTable] = self._db.execute(stmt).scalars().all()
        edges: List[GraphEdge] = [
            GraphEdge(
                Type=GraphEdgeType.relation,
                Vertice_A_Code=r.From_Code,
                Vertice_B_Code=r.To_Code,
            )
            for r in rows
        ]
        return edges

    def _get_valid_acknowledged_relations(self) -> List[GraphEdge]:
        stmt = (
            select(AcknowledgedRelationsTable)
            .filter(AcknowledgedRelationsTable.From_Acknowledged != None)
            .filter(AcknowledgedRelationsTable.To_Acknowledged != None)
            .options(
                load_only(
                    AcknowledgedRelationsTable.From_Code,
                    AcknowledgedRelationsTable.To_Code,
                )
            )
        )
        rows: List[AcknowledgedRelationsTable] = self._db.execute(stmt).scalars().all()
        edges: List[GraphEdge] = [
            GraphEdge(
                Type=GraphEdgeType.acknowledged_relation,
                Vertice_A_Code=r.From_Code,
                Vertice_B_Code=r.To_Code,
            )
            for r in rows
        ]
        return edges

    def _get_all_valid_objects_as_vertices(self) -> List[GraphVertice]:
        subq = (
            select(
                ObjectsTable,
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
            .subquery()
        )

        aliased_subq = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_subq)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.utcnow(),
                    subq.c.End_Validity == None,
                )
            )
            .order_by(desc(subq.c.Modified_Date))
            .options(
                load_only(
                    aliased_subq.Object_Type,
                    aliased_subq.Object_ID,
                    aliased_subq.Code,
                    aliased_subq.UUID,
                    aliased_subq.Title,
                ),
            )
        )

        rows: List[ObjectsTable] = self._db.execute(stmt).scalars().all()
        vertices: List[GraphVertice] = [GraphVertice.from_orm(r) for r in rows]
        return vertices


class FullGraphEndpoint(Endpoint):
    def __init__(self, path: str):
        self._path: str = path

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
        ) -> GraphResponse:
            handler: EndpointHandler = EndpointHandler(db)
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=GraphResponse,
            summary=f"A graph representation",
            description=None,
            tags=["Graph"],
        )

        return router


class FullGraphEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "full_graph"

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

        return FullGraphEndpoint(
            path=path,
        )
