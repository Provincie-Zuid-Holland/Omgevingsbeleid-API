from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference


class WerkingsgebiedBase(BaseModel):
    Werkingsgebied: str
    symbol: str


class WerkingsgebiedCreate(WerkingsgebiedBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class WerkingsgebiedUpdate(WerkingsgebiedCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class WerkingsgebiedInDBBase(WerkingsgebiedBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class WerkingsgebiedInDB(WerkingsgebiedInDBBase):
    Created_By: str
    Modified_By: str


class WerkingsgebiedInline(WerkingsgebiedInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Werkingsgebied(WerkingsgebiedInDBBase):
    """
    Full Werkingsgebied object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias


class WerkingsgebiedShortInline(BaseModel):
    ID: int
    UUID: str

    Created_By: Optional[GebruikerInline]
    Modified_by: Optional[GebruikerInline]
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Werkingsgebied: str
    symbol: str

    class Config:
        orm_mode = True
