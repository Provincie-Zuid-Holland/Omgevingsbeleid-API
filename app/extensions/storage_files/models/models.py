import uuid
from datetime import datetime

from pydantic import BaseModel


class StorageFileBasic(BaseModel):
    UUID: uuid.UUID
    Checksum: str
    Filename: str
    Content_Type: str
    Size: int
    Created_Date: datetime
    Created_By_UUID: uuid.UUID

    class Config:
        orm_mode = True
