from typing import Any, List, Optional
from app.util.legacy_helpers import to_ref_field

from pydantic import BaseModel
from pydantic.utils import GetterDict
from datetime import datetime

from .gebruiker import GebruikerInline
from .beleidskeuze import Beleidskeuze
from .maatregel import Maatregel, MaatregelInDB

# Many to many schema's
class RelatedBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        keys = Beleidskeuze.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(RelatedBeleidskeuzeGetter, self).get(key, default)


class RelatedBeleidskeuze(Beleidskeuze):
    Koppeling_Omschrijving: str

    class Config:
        orm_mode = True
        getter_dict = RelatedBeleidskeuzeGetter


class RelatedMaatregelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        keys = Maatregel.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Maatregel, key)
        else:
            return super(RelatedMaatregelGetter, self).get(key, default)


class RelatedMaatregel(MaatregelInDB):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    Koppeling_Omschrijving: str

    class Config:
        orm_mode = True
        getter_dict = RelatedMaatregelGetter


# Shared properties
class BeleidsmoduleBase(BaseModel):
    Titel: Optional[str] = None
    Besluit_Datum: Optional[str] = None


class BeleidsmoduleCreate(BeleidsmoduleBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsmoduleUpdate(BeleidsmoduleBase):
    pass


class BeleidsmoduleInDBBase(BeleidsmoduleBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Besluit_Datum: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Beleidsmodule(BeleidsmoduleInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]
    Maatregelen: List[RelatedMaatregel]

    class Config:
        allow_population_by_field_name = True


# Properties properties stored in DB
class BeleidsmoduleInDB(BeleidsmoduleInDBBase):
    pass
