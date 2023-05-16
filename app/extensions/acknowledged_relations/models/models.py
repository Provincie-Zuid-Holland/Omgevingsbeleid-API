from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, root_validator


class AcknowledgedRelationBase(BaseModel):
    Object_ID: int
    Object_Type: str
    Explanation: Optional[str]

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class RequestAcknowledgedRelation(AcknowledgedRelationBase):
    pass


class EditAcknowledgedRelation(AcknowledgedRelationBase):
    Explanation: Optional[str] = Field(None, nullable=True)
    Acknowledged: Optional[bool] = Field(None, nullable=True)
    Denied: Optional[bool] = Field(None, nullable=True)
    Deleted: Optional[bool] = Field(None, nullable=True)

    @root_validator
    def validate_denied_acknowledged_deleted(cls, values):
        denied = values.get("Denied")
        acknowledged = values.get("Acknowledged")
        deleted = values.get("Deleted")
        if sum([bool(val) for val in [denied, acknowledged, deleted]]) > 1:
            raise ValueError("Only one of Denied, Acknowledged, and Deleted can be set to True")
        return values


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    Acknowledged: Optional[datetime] = None
    Acknowledged_By_UUID: Optional[uuid.UUID] = None
    Title: Optional[str]
    Explanation: Optional[str]

    @property
    def Is_Acknowledged(self) -> bool:
        return self.Acknowledged is not None

    @property
    def Acknowledged_Date(self) -> datetime:
        return self.Acknowledged

    def disapprove(self):
        self.Acknowledged = None

    def approve(self, user_uuid: uuid.UUID, timepoint: datetime = datetime.now()):
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

    Denied: Optional[datetime]
    Deleted_At: Optional[datetime]


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
