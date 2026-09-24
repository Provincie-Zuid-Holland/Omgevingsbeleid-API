from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, aliased, load_only

from app.api.dependencies import depends_db_session
from app.api.domains.others.types import GraphEdge, GraphEdgeType, GraphResponse, GraphVertice
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from app.core.tables.objects import ObjectsTable
from app.core.tables.others import RelationsTable


class EndpointHandler:
    def __init__(self, session: Session):
        self._session: Session = session

    def handle(self) -> GraphResponse:
        vertices: list[GraphVertice] = []
        edges: list[GraphEdge] = []
        vertices, edges = self._resolve_valid_object_data()
        edges = edges + self._get_other_edges()

        return GraphResponse(
            Vertices=vertices,
            Edges=edges,
        )

    def _get_other_edges(self) -> list[GraphEdge]:
        relations: list[GraphEdge] = self._get_all_relations()
        acknowledged_relations: list[GraphEdge] = self._get_valid_acknowledged_relations()

        return relations + acknowledged_relations

    def _get_all_relations(self) -> list[GraphEdge]:
        stmt = select(RelationsTable)
        rows: Sequence[RelationsTable] = self._session.execute(stmt).scalars().all()
        edges: list[GraphEdge] = [
            GraphEdge(
                Type=GraphEdgeType.relation,
                Vertice_A_Code=r.from_code,
                Vertice_B_Code=r.to_code,
            )
            for r in rows
        ]
        return edges

    def _get_valid_acknowledged_relations(self) -> list[GraphEdge]:
        stmt = (
            select(AcknowledgedRelationsTable)
            .filter(AcknowledgedRelationsTable.from_acknowledged.is_not(None))
            .filter(AcknowledgedRelationsTable.to_acknowledged.is_not(None))
            .options(
                load_only(
                    AcknowledgedRelationsTable.from_code,
                    AcknowledgedRelationsTable.to_code,
                )
            )
        )
        rows: Sequence[AcknowledgedRelationsTable] = self._session.execute(stmt).scalars().all()
        edges: list[GraphEdge] = [
            GraphEdge(
                Type=GraphEdgeType.acknowledged_relation,
                Vertice_A_Code=r.from_code,
                Vertice_B_Code=r.to_code,
            )
            for r in rows
        ]
        return edges

    def _resolve_valid_object_data(self) -> tuple[list[GraphVertice], list[GraphEdge]]:
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
                    aliased_subq.title,
                    aliased_subq.hierarchy_code,
                ),
            )
        )

        rows: list[ObjectsTable] = list(self._session.execute(stmt).scalars().all())
        vertices: list[GraphVertice] = [GraphVertice.model_validate(r) for r in rows]

        # Use the same rows to build hierarchy_code edges
        hierarchy_code_edges: list[GraphEdge] = []
        for row in rows:
            if not row.hierarchy_code:
                continue
            hierarchy_code_edges.append(
                GraphEdge(
                    Type=GraphEdgeType.hierarchy_code,
                    Vertice_A_Code=row.code,
                    Vertice_B_Code=row.hierarchy_code,
                )
            )

        return vertices, hierarchy_code_edges


def get_full_graph_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
) -> GraphResponse:
    handler = EndpointHandler(session)
    return handler.handle()
