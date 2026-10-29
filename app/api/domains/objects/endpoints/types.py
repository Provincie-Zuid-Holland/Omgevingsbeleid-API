import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.types import AcknowledgedRelationSide


class AcknowledgedRelation(BaseModel):
    side_a: AcknowledgedRelationSide
    side_b: AcknowledgedRelationSide

    version: int
    requested_by_code: str
    created_date: datetime
    created_by_id: uuid.UUID
    modified_date: datetime
    modified_by_id: uuid.UUID

    denied: datetime | None = None
    deleted_at: datetime | None = None

    @property
    def is_acknowledged(self) -> bool:
        return self.side_a.is_acknowledged and self.side_b.is_acknowledged


def build_from_orm(orm_model, perspective_code: str) -> AcknowledgedRelation:
    """
    perspective is who requested this and will be used as the "Side_A" side
    """
    side_from: AcknowledgedRelationSide = orm_model.side_from
    side_to: AcknowledgedRelationSide = orm_model.side_to

    if perspective_code == side_from.code:
        side_a, side_b = side_from, side_to
    else:
        side_a, side_b = side_to, side_from

    return AcknowledgedRelation(
        side_a=side_a,
        side_b=side_b,
        version=orm_model.version,
        requested_by_code=orm_model.requested_by_code,
        created_date=orm_model.created_date,
        created_by_id=orm_model.created_by_id,
        modified_date=orm_model.modified_date,
        modified_by_id=orm_model.modified_by_id,
        denied=orm_model.denied,
        deleted_at=orm_model.deleted_at,
    )
