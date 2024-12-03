import uuid
from datetime import datetime

from pydantic import BaseModel, validator


class AreaBasic(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Source_UUID: uuid.UUID
    Source_Title: str
    Source_Modified_Date: datetime

    class Config:
        orm_mode = True


class WerkingsgebiedStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @validator("Cached_Title", pre=True)
    def default_empty_string(cls, v):
        return "" if v is None else v

    class Config:
        orm_mode = True
