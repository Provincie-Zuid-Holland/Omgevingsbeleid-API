import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NextObjectValidities(BaseModel):
    UUID: uuid.UUID
    Start_Validity: datetime
    End_Validity: Optional[datetime] = None
    Created_Date: datetime
    Modified_Date: datetime

    # needed for SQLAlchemy composite mapping
    __composite_nullable__ = True

    @classmethod
    def create(cls, object_uuid, start_validity, end_validity, created_date, modified_date):
        if all(v is None for v in (object_uuid, start_validity, end_validity, created_date, modified_date)):
            return None
        return cls(
            UUID=object_uuid,
            Start_Validity=start_validity,
            End_Validity=end_validity,
            Created_Date=created_date,
            Modified_Date=modified_date
        )

    # needed for SQLAlchemy composite mapping
    def __composite_values__(self):
        return (
            self.UUID,
            self.Start_Validity,
            self.End_Validity,
            self.Created_Date,
            self.Modified_Date,
        )

    class Config:
        orm_mode = True
