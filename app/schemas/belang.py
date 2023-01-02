from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict


from .beleidskeuze import BeleidskeuzeInDB, BeleidskeuzeShortInline
from app.schemas.common import BeleidskeuzeReference, GebruikerInline


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
    Weblink: Optional[str] = None
    Type: Optional[str] = None


class BelangCreate(BelangBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BelangUpdate(BelangCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


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
def reference_alias_generator(field: str) -> str:
    """
    Hack to enable manual aliassing of schema output which
    is not yet supported in FastApi
    """
    aliasses = {
        "Beleidskeuzes": "Ref_Beleidskeuzes",
        "Valid_Beleidskeuzes": "Ref_Beleidskeuzes",
    }

    if field in aliasses:
        return aliasses[field]

    return field


class Belang(BelangInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = reference_alias_generator


# Properties properties stored in DB
class BelangInDB(BelangInDBBase):
    pass
