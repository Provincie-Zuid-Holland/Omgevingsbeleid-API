import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NextObjectValidities(BaseModel):
    Object_UUID: uuid.UUID
    Start_Validity: datetime
    End_Validity: Optional[datetime]
    Created_Date: datetime
    Modified_Date: datetime