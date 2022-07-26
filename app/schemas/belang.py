from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict

from app.util.legacy_helpers import to_ref_field

from .beleidskeuze import BeleidskeuzeInDB, BeleidskeuzeShortInline
from .gebruiker import GebruikerInline

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
class BelangBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Status: Optional[str] = None
    Weblink: Optional[str] = None
    Type: Optional[str] = None


class BelangCreate(BelangBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BelangUpdate(BelangBase):
    pass


class BelangInDBBase(BelangBase):
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
class Belang(BelangInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class AmbitieInDB(AmbitieInDBBase):
    pass


# Properties properties stored in DB
class BelangInDB(BelangInDBBase):
    pass

