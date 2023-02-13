from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline


class VerordeningstructuurBase(BaseModel):
    Titel: str
    Structuur: str
    Status: Optional[str]


class VerordeningstructuurCreate(VerordeningstructuurBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class VerordeningstructuurUpdate(VerordeningstructuurCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Titel: Optional[str]
    Status: Optional[str]
    Structuur: Optional[str]


class VerordeningstructuurInDBBase(VerordeningstructuurBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class VerordeningstructuurInDB(VerordeningstructuurInDBBase):
    pass


class Verordeningstructuur(VerordeningstructuurInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
