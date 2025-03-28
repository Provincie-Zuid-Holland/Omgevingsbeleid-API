import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class AcknowledgedRelationBase(BaseModel):
    Object_ID: int
    Object_Type: str
    Explanation: Optional[str] = Field(None)

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class RequestAcknowledgedRelation(AcknowledgedRelationBase):
    pass


class EditAcknowledgedRelation(AcknowledgedRelationBase):
    Acknowledged: Optional[bool] = Field(None)
    Denied: Optional[bool] = Field(None)
    Deleted: Optional[bool] = Field(None)

    @model_validator(mode="after")
    def validate_denied_acknowledged_deleted(self):
        if sum(bool(val) for val in [self.Acknowledged, self.Denied, self.Deleted]) > 1:
            raise ValueError("Only one of Denied, Acknowledged, and Deleted can be set to True")
        return self


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    Acknowledged: Optional[datetime] = None
    Acknowledged_By_UUID: Optional[uuid.UUID] = None
    Title: Optional[str] = None
    Explanation: Optional[str] = None

    @property
    def Is_Acknowledged(self) -> bool:
        return self.Acknowledged is not None

    @property
    def Acknowledged_Date(self) -> datetime:
        return self.Acknowledged

    def disapprove(self):
        self.Acknowledged = None

    def approve(self, user_uuid: uuid.UUID, timepoint: Optional[datetime] = None):
        timepoint = timepoint or datetime.now(timezone.utc)
        if self.Is_Acknowledged:
            return

        self.Acknowledged_By_UUID = user_uuid
        self.Acknowledged = timepoint


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
