import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StorageFileBasic(BaseModel):
    UUID: uuid.UUID
    Checksum: str
    Filename: str
    Content_Type: str
    Size: int
    Created_Date: datetime
    Created_By_UUID: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
