from datetime import datetime, timezone
from typing import Annotated, List, Set

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, aliased, load_only

from app.api.dependencies import depends_db_session
from app.api.domains.others.dependencies import depends_object_by_uuid
from app.api.domains.others.types import GraphEdge, GraphEdgeType, GraphResponse, GraphVertice
from app.api.endpoint import BaseEndpointContext
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import RelationsTable


class GraphIteration(BaseModel):
    allowed_object_types: List[str]


class GraphIterationsConfig(BaseModel):
    relations: List[GraphIteration]
    acknowledged_relations: List[GraphIteration]


class ObjectGraphEndpointContext(BaseEndpointContext):
    graph_iterations: GraphIterationsConfig


class EndpointHandler:
    def __init__(
        self,
        session: Session,
        iterations_config: GraphIterationsConfig,
        object_table: ObjectsTable,
    ):
        self._session: Session = session
        self._iterations_config: GraphIterationsConfig = iterations_config
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .filter(ObjectsTable.Code.in_(codes))
            .subquery()
        )

        aliased_subq = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_subq)
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
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

        rows: List[ObjectsTable] = self._session.execute(stmt).scalars().all()
        vertices: List[GraphVertice] = [GraphVertice.model_validate(r) for r in rows]
        return vertices

    def _get_edges(self) -> List[GraphEdge]:
        relations: Set[GraphEdge] = self._get_relations()
        acknowledged_relations: Set[GraphEdge] = self._get_valid_acknowledged_relations()

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
            rows: List[RelationsTable] = self._session.execute(stmt).scalars().all()

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
                                    AcknowledgedRelationsTable.To_Code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                        and_(
                            AcknowledgedRelationsTable.To_Code.in_(search_codes),
                            or_(
                                *[
                                    AcknowledgedRelationsTable.From_Code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                    )
                )
                .filter(AcknowledgedRelationsTable.From_Code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.To_Code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.From_Acknowledged.is_not(None))
                .filter(AcknowledgedRelationsTable.To_Acknowledged.is_not(None))
                .options(
                    load_only(
                        AcknowledgedRelationsTable.From_Code,
                        AcknowledgedRelationsTable.To_Code,
                    )
                )
            )

            rows: List[AcknowledgedRelationsTable] = self._session.execute(stmt).scalars().all()

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


def get_object_graph_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
    object_table: Annotated[ObjectsTable, Depends(depends_object_by_uuid)],
    context: Annotated[ObjectGraphEndpointContext, Depends()],
) -> GraphResponse:
    handler = EndpointHandler(session, context.graph_iterations, object_table)
    return handler.handle()
