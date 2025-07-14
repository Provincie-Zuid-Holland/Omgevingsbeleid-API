from typing import Annotated, List, Sequence

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import depends_db_session
from app.api.domains.objects.types import ReadRelation
from app.api.endpoint import BaseEndpointContext
from app.core.tables.others import RelationsTable


def _format_rows(object_code: str, table_rows: Sequence[RelationsTable]) -> List[ReadRelation]:
    result: List[ReadRelation] = []

    for row in table_rows:
        # Need to determine which the relation is based on my_code
        title: str = row.FromObjectStatics.Cached_Title
        relation_code: str = row.From_Code
        if relation_code == object_code:
            relation_code = row.To_Code
            title = row.ToObjectStatics.Cached_Title

        # Decode the code into object_type and ID, as that is easier to use for the client
        relation_object_type, relation_id = relation_code.split("-", 1)

        response_model = ReadRelation(
            Object_ID=relation_id,
            Object_Type=relation_object_type,
            Description=row.Description,
            Title=title,
        )
        result.append(response_model)

    return result


class RelationsListEndpointContext(BaseEndpointContext):
    object_type: str


def get_relations_list_endpoint(
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[RelationsListEndpointContext, Depends()],
) -> List[ReadRelation]:
    object_code: str = f"{context.object_type}-{lineage_id}"

    stmt = (
        select(RelationsTable)
        .filter(
            or_(
                RelationsTable.From_Code == object_code,
                RelationsTable.To_Code == object_code,
            )
        )
        .options(
            selectinload(RelationsTable.FromObjectStatics),
            selectinload(RelationsTable.ToObjectStatics),
        )
    )
    table_rows: Sequence[RelationsTable] = session.scalars(stmt).all()

    response: List[ReadRelation] = _format_rows(object_code, table_rows)
    return response
