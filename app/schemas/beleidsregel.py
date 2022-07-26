from typing import Any, List, Optional
from app.schemas.ambitie import BeleidskeuzeShortInline

from pydantic import BaseModel
from pydantic.utils import GetterDict
from datetime import datetime

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
class BeleidsregelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None
    Externe_URL: Optional[str] = None


class BeleidsregelCreate(BeleidsregelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsregelUpdate(BeleidsregelBase):
    pass


class BeleidsregelInDBBase(BeleidsregelBase):
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
class Beleidsregel(BeleidsregelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
    Beleidskeuzes: List[RelatedBeleidskeuze]


# Properties properties stored in DB
class BeleidsregelInDB(BeleidsregelInDBBase):
    pass
