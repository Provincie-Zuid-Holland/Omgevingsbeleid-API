import uuid
from datetime import datetime

from pydantic import BaseModel


class StorageFileBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Filename: str
    Size: int

    class Config:
        orm_mode = True
