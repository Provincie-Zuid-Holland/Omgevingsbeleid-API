from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, to_ref_field


# Shared properties
class VerordeningstructuurBase(BaseModel):
    Titel: Optional[str] = None
    Structuur: Optional[str] = None
    Status: Optional[str] = None


class VerordeningstructuurCreate(VerordeningstructuurBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class VerordeningstructuurUpdate(VerordeningstructuurCreate):
    pass


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


# Properties to return to client
class Verordeningstructuur(VerordeningstructuurInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class VerordeningstructuurInDB(VerordeningstructuurInDBBase):
    pass
