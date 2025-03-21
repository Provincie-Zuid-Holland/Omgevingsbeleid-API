import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NextObjectValidities(BaseModel):
    UUID: uuid.UUID
    Start_Validity: datetime
    End_Validity: Optional[datetime] = None
    Created_Date: datetime
    Modified_Date: datetime

    model_config = ConfigDict(from_attributes=True)
