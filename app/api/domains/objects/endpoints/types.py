import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.core.types import AcknowledgedRelationSide


class AcknowledgedRelation(BaseModel):
    Side_A: AcknowledgedRelationSide
    Side_B: AcknowledgedRelationSide

    Version: int
    Requested_By_Code: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_Date: datetime
    Modified_By_UUID: uuid.UUID

    Denied: Optional[datetime] = None
    Deleted_At: Optional[datetime] = None

    @property
    def Is_Acknowledged(self) -> bool:
        return self.Side_A.Is_Acknowledged and self.Side_B.Is_Acknowledged


def build_from_orm(orm_model, perspective_code: str) -> AcknowledgedRelation:
    """
    perspective is who requested this and will be used as the "Side_A" side
    """
    side_from: AcknowledgedRelationSide = orm_model.side_from
    side_to: AcknowledgedRelationSide = orm_model.side_to

    if perspective_code == side_from.Code:
        side_a, side_b = side_from, side_to
    else:
        side_a, side_b = side_to, side_from

    return AcknowledgedRelation(
        Side_A=side_a,
        Side_B=side_b,
        Version=orm_model.Version,
        Requested_By_Code=orm_model.Requested_By_Code,
        Created_Date=orm_model.Created_Date,
        Created_By_UUID=orm_model.Created_By_UUID,
        Modified_Date=orm_model.Modified_Date,
        Modified_By_UUID=orm_model.Modified_By_UUID,
        Denied=orm_model.Denied,
        Deleted_At=orm_model.Deleted_At,
    )
