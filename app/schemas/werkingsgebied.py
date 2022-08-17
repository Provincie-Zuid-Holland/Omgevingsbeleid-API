from typing import List

from pydantic import BaseModel
from datetime import datetime
from .relationships import GebruikerInline, RelatedBeleidskeuze

from app.util.legacy_helpers import to_ref_field


# Shared properties
class WerkingsgebiedBase(BaseModel):
    Werkingsgebied: str


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


# Properties to return to client
class Werkingsgebied(WerkingsgebiedInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class WerkingsgebiedInDB(WerkingsgebiedInDBBase):
    pass
