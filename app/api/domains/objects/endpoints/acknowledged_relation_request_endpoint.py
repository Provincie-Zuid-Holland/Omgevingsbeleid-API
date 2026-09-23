from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.dependencies import depends_db_session
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.types import ResponseOK
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from app.core.tables.users import UsersTable
from app.core.types import AcknowledgedRelationBase, AcknowledgedRelationSide


class RequestAcknowledgedRelation(AcknowledgedRelationBase):
    pass


class AcknowledgedRelationRequestEndpointContext(BaseEndpointContext):
    object_type: str
    allowed_object_types: list[str]


def get_acknowledged_relation_request_endpoint(
    lineage_id: int,
    object_in: RequestAcknowledgedRelation,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    context: Annotated[AcknowledgedRelationRequestEndpointContext, Depends()],
) -> ResponseOK:
    if object_in.object_type not in context.allowed_object_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Object_Type")

    timepoint: datetime = datetime.now(UTC)

    my_side = AcknowledgedRelationSide(
        object_id=lineage_id,
        object_type=context.object_type,
        acknowledged=timepoint,
        acknowledged_by_uuid=user.UUID,
        explanation=object_in.explanation,
    )
    their_side = AcknowledgedRelationSide(
        object_id=object_in.object_id,
        object_type=object_in.object_type,
    )

    ack_table = AcknowledgedRelationsTable(
        requested_by_code=my_side.code,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=user.UUID,
    )
    ack_table.with_sides(my_side, their_side)

    existing_request: AcknowledgedRelationsTable | None = (
        session.query(AcknowledgedRelationsTable)
        .filter(
            and_(
                AcknowledgedRelationsTable.from_code == ack_table.from_code,
                AcknowledgedRelationsTable.to_code == ack_table.to_code,
                AcknowledgedRelationsTable.denied.is_(None),
                AcknowledgedRelationsTable.deleted_at.is_(None),
            )
        )
        .first()
    )

    if existing_request:
        if existing_request.is_acknowledged or existing_request.requested_by_code == my_side.code:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Existing relation(request), either edit or delete first",
            )

        # assume we can approve the existing request as both sides have acted
        existing_request.apply_side(my_side)
        existing_request.Modified_Date = timepoint
        existing_request.Modified_By_UUID = user.UUID

        session.add(existing_request)
        session.flush()
        session.commit()
        return ResponseOK(message="Updated existing request")

    # Query for max version so we can increment by 1
    max_version = (
        session.query(func.max(AcknowledgedRelationsTable.version))
        .filter(
            and_(
                AcknowledgedRelationsTable.from_code == ack_table.from_code,
                AcknowledgedRelationsTable.to_code == ack_table.to_code,
            )
        )
        .scalar()
    )

    if max_version is not None:
        ack_table.version = max_version + 1

    session.add(ack_table)
    session.flush()
    session.commit()

    return ResponseOK(message="OK")
