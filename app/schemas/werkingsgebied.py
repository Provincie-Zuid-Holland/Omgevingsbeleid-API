from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict
from datetime import datetime

from app.util.legacy_helpers import to_ref_field

from .gebruiker import GebruikerInline
from .beleidskeuze import BeleidskeuzeInDB, BeleidskeuzeShortInline

# Many to many schema's
class RelatedBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        keys = BeleidskeuzeInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(RelatedBeleidskeuzeGetter, self).get(key, default)


class RelatedBeleidskeuze(BeleidskeuzeShortInline):
    class Config:
        getter_dict = RelatedBeleidskeuzeGetter


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


class WerkingsgebiedShortInline(BaseModel):
    ID: int
    UUID: str
    Werkingsgebied: str

    class Config:
        orm_mode = True

