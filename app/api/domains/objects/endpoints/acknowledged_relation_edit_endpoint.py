from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from pydantic import Field, model_validator
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.objects.repositories.acknowledged_relations_repository import AcknowledgedRelationsRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.types import ResponseOK
from app.core.tables.acknowledged_relations import AcknowledgedRelationsTable
from app.core.tables.users import UsersTable
from app.core.types import AcknowledgedRelationBase, AcknowledgedRelationSide


class EditAcknowledgedRelation(AcknowledgedRelationBase):
    Acknowledged: Optional[bool] = Field(None)
    Denied: Optional[bool] = Field(None)
    Deleted: Optional[bool] = Field(None)

    @model_validator(mode="after")
    def validate_denied_acknowledged_deleted(self):
        if sum(bool(val) for val in [self.Acknowledged, self.Denied, self.Deleted]) > 1:
            raise ValueError("Only one of Denied, Acknowledged, and Deleted can be set to True")
        return self


class AcknowledgedRelationEditEndpointContext(BaseEndpointContext):
    object_type: str


@inject
async def post_acknowledged_relation_edit_endpoint(
    lineage_id: int,
    object_in: EditAcknowledgedRelation,
    user: Annotated[UsersTable, Depends(depends_current_user)],
    repository: Annotated[
        AcknowledgedRelationsRepository, Depends(Provide[ApiContainer.acknowledged_relations_repository])
    ],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[AcknowledgedRelationEditEndpointContext, Depends()],
) -> ResponseOK:
    object_code: str = f"{context.object_type}-{lineage_id}"
    timepoint: datetime = datetime.now(timezone.utc)

    relation: Optional[AcknowledgedRelationsTable] = repository.get_by_codes(
        object_code,
        object_in.Code,
    )
    if not relation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Acknowledged relation not found")

    # We just edit a side and then push it back in to the table
    side: AcknowledgedRelationSide = relation.get_side(object_code)

    if object_in.Explanation is not None:
        side.Explanation = object_in.Explanation
    if object_in.Acknowledged == False:
        side.disapprove()
    if object_in.Acknowledged == True:
        side.approve(user.UUID)

    relation.apply_side(side)
    relation.Modified_Date = timepoint
    relation.Modified_By_UUID = user.UUID

    if object_in.Denied == True:
        relation.deny()
    if object_in.Deleted == True:
        relation.delete()

    db.add(relation)
    db.flush()
    db.commit()

    return ResponseOK(message="OK")
