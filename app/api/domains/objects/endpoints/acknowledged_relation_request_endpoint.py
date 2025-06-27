from datetime import datetime, timezone
from typing import Annotated, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
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
    allowed_object_types: List[str]


@inject
async def get_acknowledged_relation_request_endpoint(
    lineage_id: int,
    object_in: RequestAcknowledgedRelation,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[AcknowledgedRelationRequestEndpointContext, Depends()],
) -> ResponseOK:
    if object_in.Object_Type not in context.allowed_object_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid Object_Type")

    timepoint: datetime = datetime.now(timezone.utc)

    my_side = AcknowledgedRelationSide(
        Object_ID=lineage_id,
        Object_Type=context.object_type,
        Acknowledged=timepoint,
        Acknowledged_By_UUID=user.UUID,
        Explanation=object_in.Explanation,
    )
    their_side = AcknowledgedRelationSide(
        Object_ID=object_in.Object_ID,
        Object_Type=object_in.Object_Type,
    )

    ack_table = AcknowledgedRelationsTable(
        Requested_By_Code=my_side.Code,
        Created_Date=timepoint,
        Created_By_UUID=user.UUID,
        Modified_Date=timepoint,
        Modified_By_UUID=user.UUID,
    )
    ack_table.with_sides(my_side, their_side)

    existing_request: Optional[AcknowledgedRelationsTable] = (
        db.query(AcknowledgedRelationsTable)
        .filter(
            and_(
                AcknowledgedRelationsTable.From_Code == ack_table.From_Code,
                AcknowledgedRelationsTable.To_Code == ack_table.To_Code,
                AcknowledgedRelationsTable.Denied.is_(None),
                AcknowledgedRelationsTable.Deleted_At.is_(None),
            )
        )
        .first()
    )

    if existing_request:
        if existing_request.Is_Acknowledged or existing_request.Requested_By_Code == my_side.Code:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Existing relation(request), either edit or delete first",
            )

        # assume we can approve the existing request as both sides have acted
        existing_request.apply_side(my_side)
        existing_request.Modified_Date = timepoint
        existing_request.Modified_By_UUID = user.UUID

        db.add(existing_request)
        db.flush()
        db.commit()
        return ResponseOK(message="Updated existing request")

    # Query for max version so we can increment by 1
    max_version = (
        db.query(func.max(AcknowledgedRelationsTable.Version))
        .filter(
            and_(
                AcknowledgedRelationsTable.From_Code == ack_table.From_Code,
                AcknowledgedRelationsTable.To_Code == ack_table.To_Code,
            )
        )
        .scalar()
    )

    if max_version is not None:
        ack_table.Version = max_version + 1

    db.add(ack_table)
    db.flush()
    db.commit()

    return ResponseOK(message="OK")
