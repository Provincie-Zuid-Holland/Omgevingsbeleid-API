import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Werkingsgebied(BaseModel):
    ID: Optional[int] = None
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str
    Start_Validity: Optional[datetime] = Field(None)
    End_Validity: Optional[datetime] = Field(None)
    Geometry_Hash: Optional[str] = Field(None)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
