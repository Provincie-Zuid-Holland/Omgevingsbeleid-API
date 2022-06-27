from typing import Optional, List, Any

from pydantic import BaseModel
from pydantic.utils import GetterDict

from datetime import datetime

from .gebruiker import GebruikerInline

# from .beleidskeuze import BeleidskeuzeShortInline

from app.util.legacy_helpers import to_ref_field

# Many to many schema's


class AmbitieBeleidskeuzesGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        keys = BeleidskeuzeShortInline.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(AmbitieBeleidskeuzesGetter, self).get(key, default)


class BeleidskeuzeShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True
        getter_dict = AmbitieBeleidskeuzesGetter


# Shared properties
class AmbitieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class AmbitieCreate(AmbitieBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class AmbitieUpdate(AmbitieBase):
    pass


class AmbitieInDBBase(AmbitieBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Omschrijving: str
    Weblink: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Ambitie(AmbitieInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[BeleidskeuzeShortInline]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class AmbitieInDB(AmbitieInDBBase):
    pass
