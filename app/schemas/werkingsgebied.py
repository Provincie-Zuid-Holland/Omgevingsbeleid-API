from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import BeleidskeuzeReference, GebruikerInline, valid_ref_alias


class WerkingsgebiedBase(BaseModel):
    Werkingsgebied: str
    symbol: str


class WerkingsgebiedCreate(WerkingsgebiedBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class WerkingsgebiedUpdate(WerkingsgebiedBase):
    pass


class WerkingsgebiedInDBBase(WerkingsgebiedBase):
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


class WerkingsgebiedInDB(WerkingsgebiedInDBBase):
    pass


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
