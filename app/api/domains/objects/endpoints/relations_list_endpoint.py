from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import depends_db_session
from app.api.domains.objects.types import ReadRelation
from app.api.endpoint import BaseEndpointContext
from app.core.tables.others import RelationsTable


def _format_rows(object_code: str, table_rows: Sequence[RelationsTable]) -> list[ReadRelation]:
    result: list[ReadRelation] = []

    for row in table_rows:
        # Need to determine which the relation is based on my_code
        title: str = row.from_object_statics.cached_title
        relation_code: str = row.from_code
        if relation_code == object_code:
            relation_code = row.to_code
            title = row.to_object_statics.cached_title

        # Decode the code into object_type and ID, as that is easier to use for the client
        relation_object_type, relation_id = relation_code.split("-", 1)

        response_model = ReadRelation(
            object_id=relation_id,
            object_type=relation_object_type,
            description=row.description,
            title=title,
        )
        result.append(response_model)

    return result


class RelationsListEndpointContext(BaseEndpointContext):
    object_type: str


def get_relations_list_endpoint(
    lineage_id: int,
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[RelationsListEndpointContext, Depends()],
) -> list[ReadRelation]:
    object_code: str = f"{context.object_type}-{lineage_id}"

    stmt = (
        select(RelationsTable)
        .filter(
            or_(
                RelationsTable.from_code == object_code,
                RelationsTable.to_code == object_code,
            )
        )
        .options(
            selectinload(RelationsTable.from_object_statics),
            selectinload(RelationsTable.to_object_statics),
        )
    )
    table_rows: Sequence[RelationsTable] = session.scalars(stmt).all()

    response: list[ReadRelation] = _format_rows(object_code, table_rows)
    return response
