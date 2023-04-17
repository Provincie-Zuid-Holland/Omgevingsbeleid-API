from datetime import datetime
import uuid
from pydantic import BaseModel


class Werkingsgebied(BaseModel):
    ID: int
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
