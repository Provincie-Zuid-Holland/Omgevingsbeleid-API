from datetime import UTC, datetime
from typing import Annotated

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
    allowed_object_types: list[str]


class GraphIterationsConfig(BaseModel):
    relations: list[GraphIteration]
    acknowledged_relations: list[GraphIteration]


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
        edges: list[GraphEdge] = self._get_edges()
        vertices: list[GraphVertice] = self._get_vertices_for_edges(edges)

        return GraphResponse(
            Vertices=vertices,
            Edges=edges,
        )

    def _get_vertices_for_edges(self, edges: list[GraphEdge]) -> list[GraphVertice]:
        codes: set[str] = set()
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
                    partition_by=ObjectsTable.code,
                    order_by=desc(ObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(ObjectsTable)
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
            .filter(ObjectsTable.code.in_(codes))
            .subquery()
        )

        aliased_subq = aliased(ObjectsTable, subq)
        stmt = (
            select(aliased_subq)
            .filter(subq.c._row_number == 1)
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
            .order_by(desc(subq.c.modified_date))
            .options(
                load_only(
                    aliased_subq.object_type,
                    aliased_subq.object_id,
                    aliased_subq.code,
                    aliased_subq.id,
                    aliased_subq.Title,
                ),
            )
        )

        rows: list[ObjectsTable] = self._session.execute(stmt).scalars().all()
        vertices: list[GraphVertice] = [GraphVertice.model_validate(r) for r in rows]
        return vertices

    def _get_edges(self) -> list[GraphEdge]:
        relations: set[GraphEdge] = self._get_relations()
        acknowledged_relations: set[GraphEdge] = self._get_valid_acknowledged_relations()

        return list(set.union(relations, acknowledged_relations))

    def _get_relations(self) -> set[GraphEdge]:
        search_codes: set[str] = {
            self._object.code,
        }
        ignore_codes: set[str] = set()
        edges: set[GraphEdge] = set()

        for iteration_config in self._iterations_config.relations:
            if not search_codes:
                break

            stmt = (
                select(RelationsTable)
                .filter(
                    or_(
                        and_(
                            RelationsTable.from_code.in_(search_codes),
                            or_(
                                *[
                                    RelationsTable.to_code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                        and_(
                            RelationsTable.to_code.in_(search_codes),
                            or_(
                                *[
                                    RelationsTable.from_code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                    )
                )
                .filter(RelationsTable.from_code.not_in(ignore_codes))
                .filter(RelationsTable.to_code.not_in(ignore_codes))
            )
            rows: list[RelationsTable] = self._session.execute(stmt).scalars().all()

            # Update the search and ignore codes for the next iteration
            ignore_codes = set.union(ignore_codes, search_codes)
            search_codes = set()

            for row in rows:
                edges.add(
                    GraphEdge(
                        Type=GraphEdgeType.relation,
                        Vertice_A_Code=row.from_code,
                        Vertice_B_Code=row.to_code,
                    )
                )

                # Just add everything to search codes for now
                # We intersect it later with ignore codes to only search for something we have not searched for before
                search_codes.add(row.from_code)
                search_codes.add(row.to_code)

            # Remove everything from search_codes that is already in ignore_codes
            search_codes = set.difference(search_codes, ignore_codes)

        return edges

    def _get_valid_acknowledged_relations(self) -> set[GraphEdge]:
        search_codes: set[str] = {
            self._object.code,
        }
        ignore_codes: set[str] = set()
        edges: set[GraphEdge] = set()

        for iteration_config in self._iterations_config.acknowledged_relations:
            if not search_codes:
                break

            stmt = (
                select(AcknowledgedRelationsTable)
                .filter(
                    or_(
                        and_(
                            AcknowledgedRelationsTable.from_code.in_(search_codes),
                            or_(
                                *[
                                    AcknowledgedRelationsTable.to_code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                        and_(
                            AcknowledgedRelationsTable.to_code.in_(search_codes),
                            or_(
                                *[
                                    AcknowledgedRelationsTable.from_code.like(f"{object_type}-%")
                                    for object_type in iteration_config.allowed_object_types
                                ],
                            ).self_group(),
                        ).self_group(),
                    )
                )
                .filter(AcknowledgedRelationsTable.from_code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.to_code.not_in(ignore_codes))
                .filter(AcknowledgedRelationsTable.from_acknowledged.is_not(None))
                .filter(AcknowledgedRelationsTable.to_acknowledged.is_not(None))
                .options(
                    load_only(
                        AcknowledgedRelationsTable.from_code,
                        AcknowledgedRelationsTable.to_code,
                    )
                )
            )

            rows: list[AcknowledgedRelationsTable] = self._session.execute(stmt).scalars().all()

            # Update the search and ignore codes for the next iteration
            ignore_codes = set.union(ignore_codes, search_codes)
            search_codes = set()

            for row in rows:
                edges.add(
                    GraphEdge(
                        Type=GraphEdgeType.acknowledged_relation,
                        Vertice_A_Code=row.from_code,
                        Vertice_B_Code=row.to_code,
                    )
                )

                # Just add everything to search codes for now
                # We intersect it later with ignore codes to only search for something we have not searched for before
                search_codes.add(row.from_code)
                search_codes.add(row.to_code)

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
