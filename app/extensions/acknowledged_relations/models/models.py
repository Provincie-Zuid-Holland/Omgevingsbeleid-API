from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field, validator


class AcknowledgedRelationBase(BaseModel):
    Object_ID: int
    Object_Type: str
    Title: str
    Explanation: str

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class RequestAcknowledgedRelation(AcknowledgedRelationBase):
    pass


class EditAcknowledgedRelation(AcknowledgedRelationBase):
    Title: Optional[str] = Field(None, nullable=True)
    Explanation: Optional[str] = Field(None, nullable=True)
    Acknowledged: Optional[bool] = Field(None, nullable=True)
    Denied: Optional[bool] = Field(None, nullable=True)
    Deleted_At: Optional[bool] = Field(None, nullable=True)

    @validator("Denied", always=True)
    def validate_denied_and_acknowledged(cls, denied, values):
        acknowledged = values.get("Acknowledged")
        if denied is True and acknowledged is True:
            raise ValueError("Denied and Acknowledged cannot both be set to True")
        return denied


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    Acknowledged: Optional[datetime] = None
    Acknowledged_By_UUID: Optional[uuid.UUID] = None
    Title: str = ""  # TODO: why? ""
    Explanation: str = ""

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

    Requested_By_Code: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_Date: datetime
    Modified_By_UUID: uuid.UUID

    Denied: Optional[datetime]
    Deleted_At: Optional[datetime]

    @property
    def Is_Acknowledged(self) -> bool:
        if self.Denied:
            return False

        return self.Side_A.Is_Acknowledged and self.Side_B.Is_Acknowledged

    @property
    def Is_Denied(self) -> bool:
        return self.Denied is not None

    @property
    def Is_Deleted(self) -> bool:
        return self.Deleted_At is not None


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
        Requested_By_Code=orm_model.Requested_By_Code,
        Created_Date=orm_model.Created_Date,
        Created_By_UUID=orm_model.Created_By_UUID,
        Modified_Date=orm_model.Modified_Date,
        Modified_By_UUID=orm_model.Modified_By_UUID,
        Denied=orm_model.Denied,
    )
