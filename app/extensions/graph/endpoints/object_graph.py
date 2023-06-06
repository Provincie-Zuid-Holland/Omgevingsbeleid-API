from typing import List, Set
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc, select, func, or_, and_
from sqlalchemy.orm import Session, aliased, load_only

from app.core.dependencies import depends_db
from app.dynamic.db.objects_table import ObjectsTable
from app.dynamic.dependencies import (
    depends_object_by_uuid,
)
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


class GraphIteration(BaseModel):
    allowed_object_types: List[str]


class GraphIterationsConfig(BaseModel):
    relations: List[GraphIteration]
    acknowledged_relations: List[GraphIteration]


class EndpointHandler:
    def __init__(
        self,
        iterations_config: GraphIterationsConfig,
        db: Session,
        object_table: ObjectsTable,
    ):
        self._iterations_config: GraphIterationsConfig = iterations_config
        self._db: Session = db
        self._object = object_table

    def handle(self) -> GraphResponse:
        edges: List[GraphEdge] = self._get_edges()
        vertices: List[GraphVertice] = self._get_vertices_for_edges(edges)

        return GraphResponse(
            Vertices=vertices,
            Edges=edges,
        )

    def _get_vertices_for_edges(self, edges: List[GraphEdge]) -> List[GraphVertice]:
        codes: Set[str] = set()
        for edge in edges:
            codes.add(edge.Vertice_A_Code)
            codes.add(edge.Vertice_B_Code)

        if not codes:
            return []

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
            .filter(ObjectsTable.Start_Validity <= datetime.now())
            .filter(ObjectsTable.Code.in_(codes))
            .subquery()
        )

        aliased_subq = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_subq)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(),
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

    def _get_edges(self) -> List[GraphEdge]:
        relations: Set[GraphEdge] = self._get_relations()
        acknowledged_relations: Set[
            GraphEdge
        ] = self._get_valid_acknowledged_relations()

        return list(set.union(relations, acknowledged_relations))

    def _get_relations(self) -> Set[GraphEdge]:
        search_codes: Set[str] = set(
            [
                self._object.Code,
            ]
        )
        ignore_codes: Set[str] = set()
        edges: Set[GraphEdge] = set()

        for iteration_config in self._iterations_config.relations:
            if not search_codes:
                break

            stmt = (
                select(RelationsTable)
                .filter(
                    or_(
                        and_(
                            RelationsTable.From_Code.in_(search_codes),
                            or_(
                                *[
                                    RelationsTable.To_Code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                        and_(
                            RelationsTable.To_Code.in_(search_codes),
                            or_(
                                *[
                                    RelationsTable.From_Code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                    )
                )
                .filter(RelationsTable.From_Code.not_in(ignore_codes))
                .filter(RelationsTable.To_Code.not_in(ignore_codes))
            )
            rows: List[RelationsTable] = self._db.execute(stmt).scalars().all()

            # Update the search and ignore codes for the next iteration
            ignore_codes = set.union(ignore_codes, search_codes)
            search_codes = set()

            for row in rows:
                edges.add(
                    GraphEdge(
                        Type=GraphEdgeType.relation,
                        Vertice_A_Code=row.From_Code,
                        Vertice_B_Code=row.To_Code,
                    )
                )

                # Just add everything to search codes for now
                # We intersect it later with ignore codes to only search for something we have not searched for before
                search_codes.add(row.From_Code)
                search_codes.add(row.To_Code)

            # Remove everything from search_codes that is already in ignore_codes
            search_codes = set.difference(search_codes, ignore_codes)

        return edges

    def _get_valid_acknowledged_relations(self) -> Set[GraphEdge]:
        search_codes: Set[str] = set(
            [
                self._object.Code,
            ]
        )
        ignore_codes: Set[str] = set()
        edges: Set[GraphEdge] = set()

        for iteration_config in self._iterations_config.acknowledged_relations:
            if not search_codes:
                break

            stmt = (
                select(AcknowledgedRelationsTable)
                .filter(
                    or_(
                        and_(
                            AcknowledgedRelationsTable.From_Code.in_(search_codes),
                            or_(
                                *[
                                    AcknowledgedRelationsTable.To_Code.like(
                                        f"{object_type}-%"
                                    )
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                        and_(
                            AcknowledgedRelationsTable.To_Code.in_(search_codes),
                            or_(
                                *[
                                    AcknowledgedRelationsTable.From_Code.like(
                                        f"{object_type}-%"
                                    )
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                    )
                )
                .filter(AcknowledgedRelationsTable.From_Code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.To_Code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.From_Acknowledged != None)
                .filter(AcknowledgedRelationsTable.To_Acknowledged != None)
                .options(
                    load_only(
                        AcknowledgedRelationsTable.From_Code,
                        AcknowledgedRelationsTable.To_Code,
                    )
                )
            )

            rows: List[AcknowledgedRelationsTable] = (
                self._db.execute(stmt).scalars().all()
            )

            # Update the search and ignore codes for the next iteration
            ignore_codes = set.union(ignore_codes, search_codes)
            search_codes = set()

            for row in rows:
                edges.add(
                    GraphEdge(
                        Type=GraphEdgeType.acknowledged_relation,
                        Vertice_A_Code=row.From_Code,
                        Vertice_B_Code=row.To_Code,
                    )
                )

                # Just add everything to search codes for now
                # We intersect it later with ignore codes to only search for something we have not searched for before
                search_codes.add(row.From_Code)
                search_codes.add(row.To_Code)

            # Remove everything from search_codes that is already in ignore_codes
            search_codes = set.difference(search_codes, ignore_codes)

        return edges


class ObjectGraphEndpoint(Endpoint):
    def __init__(self, path: str, iterations_config: GraphIterationsConfig):
        self._path: str = path
        self._iterations_config: GraphIterationsConfig = iterations_config

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            db: Session = Depends(depends_db),
            object_table: ObjectsTable = Depends(depends_object_by_uuid),
        ) -> GraphResponse:
            handler: EndpointHandler = EndpointHandler(
                self._iterations_config, db, object_table
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["GET"],
            response_model=GraphResponse,
            summary=f"A graph representation of an object",
            description=None,
            tags=["Graph"],
        )

        return router


class ObjectGraphEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "object_graph"

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

        iterations_config = GraphIterationsConfig.parse_obj(
            resolver_config.get("graph_iterations")
        )

        return ObjectGraphEndpoint(
            path=path,
            iterations_config=iterations_config,
        )
