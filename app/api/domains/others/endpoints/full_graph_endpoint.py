from datetime import datetime, timezone
from typing import Annotated, List

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
        vertices: List[GraphVertice] = self._get_all_valid_objects_as_vertices()
        edges: List[GraphEdge] = self._get_all_edges()

        return GraphResponse(
            Vertices=vertices,
            Edges=edges,
        )

    def _get_all_edges(self) -> List[GraphEdge]:
        relations: List[GraphEdge] = self._get_all_relations()
        acknowledged_relations: List[GraphEdge] = self._get_valid_acknowledged_relations()

        return relations + acknowledged_relations

    def _get_all_relations(self) -> List[GraphEdge]:
        stmt = select(RelationsTable)
        rows: List[RelationsTable] = self._session.execute(stmt).scalars().all()
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
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
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


def get_full_graph_endpoint(
    session: Annotated[Session, Depends(depends_db_session)],
) -> GraphResponse:
    handler = EndpointHandler(session)
    return handler.handle()
