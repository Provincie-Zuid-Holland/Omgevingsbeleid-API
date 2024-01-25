import uuid
from datetime import datetime

from pydantic import BaseModel


class AreaBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Source_Title: str

    class Config:
        orm_mode = True
