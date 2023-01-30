from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.base import Status as StatusEnum
from app.schemas.common import GebruikerInline, to_ref_field


class VerordeningstructuurBase(BaseModel):
    Titel: str
    Structuur: str
    Status: StatusEnum


class VerordeningstructuurCreate(VerordeningstructuurBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class VerordeningstructuurUpdate(VerordeningstructuurCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Titel: Optional[str]
    Status: Optional[StatusEnum]
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

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field
