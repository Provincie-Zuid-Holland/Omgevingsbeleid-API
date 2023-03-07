from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class WerkingsgebiedShort(BaseModel):
    UUID: uuid.UUID = Field(..., alias="Werkingsgebied_UUID")
    Description: str = Field(default="")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class werkingsgebied(BaseModel):
    ID: int
    UUID: uuid.UUID = Field(..., alias="Werkingsgebied_UUID")
    Created_Date: datetime
    Modified_Date: datetime
    Werkingsgebied: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
