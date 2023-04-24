from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel

from app.extensions.users.model import UserShort


class RegulationTypes(str, Enum):
    belang = "Nationaal Belang"
    taken = "Wettelijke taken en bevoegdheden"


class Regulation(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Title: str
    Type: str

    Created_By: Optional[UserShort]
    Modified_By: Optional[UserShort]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
