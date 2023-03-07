from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel


class AcknowledgedRelationSide(BaseModel):
    ID: int
    Object_Type: str
    Acknowledged: bool = False
    Acknowledged_Date: Optional[datetime] = None
    Acknowledged_By_UUID: Optional[uuid.UUID] = None
    Title: str = ""
    Explanation: str = ""

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.ID}"

    def disapprove(self):
        self.Acknowledged = False

    def approve(self, timepoint: datetime, user_uuid: uuid.UUID):
        if self.Acknowledged == True:
            return
        self.Acknowledged = True
        self.Acknowledged_By_UUID = user_uuid
        self.Acknowledged_Date = timepoint


class AcknowledgedRelation(BaseModel):
    Side_A: AcknowledgedRelationSide
    Side_B: AcknowledgedRelationSide

    Requested_By_Code: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_Date: datetime
    Modified_By_UUID: uuid.UUID
