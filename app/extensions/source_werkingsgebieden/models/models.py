import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Werkingsgebied(BaseModel):
    ID: Optional[int]
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str
    Start_Validity: Optional[datetime] = Field(None)
    End_Validity: Optional[datetime] = Field(None)
    Geometry_Hash: Optional[str] = Field(None)

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
