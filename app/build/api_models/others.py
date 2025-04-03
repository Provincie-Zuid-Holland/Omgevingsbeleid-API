import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class HierarchyStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @field_validator("Cached_Title", mode="before")
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)


class StorageFileBasic(BaseModel):
    UUID: uuid.UUID
    Checksum: str
    Filename: str
    Content_Type: str
    Size: int
    Created_Date: datetime
    Created_By_UUID: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

