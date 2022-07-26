from typing import Any, List, Optional
from app.util.legacy_helpers import to_ref_field

from pydantic import BaseModel
from pydantic.utils import GetterDict
from datetime import datetime

from .gebruiker import GebruikerInline

# Many to many schema's
class RelatedBeleidsmoduleGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidsmodule import BeleidsmoduleInDB

        keys = BeleidsmoduleInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidskeuze, key)
        else:
            return super(RelatedBeleidsmoduleGetter, self).get(key, default)


class RelatedBeleidsmodule(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = RelatedBeleidsmoduleGetter


class RelatedBeleidsdoelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidsdoel import BeleidsdoelInDB

        keys = BeleidsdoelInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Beleidsdoel, key)
        else:
            return super(RelatedBeleidsdoelGetter, self).get(key, default)


class RelatedBeleidsdoel(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = RelatedBeleidsdoelGetter


class RelatedMaatregelGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .maatregel import MaatregelInDB

        keys = MaatregelInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Maatregel, key)
        else:
            return super(RelatedMaatregelGetter, self).get(key, default)


class RelatedMaatregel(BaseModel):
    ID: int
    UUID: str
    Titel: str
    Koppeling_Omschrijving: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = RelatedMaatregelGetter


# Shared properties
class BeleidskeuzeBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving_Keuze: Optional[str] = None
    Omschrijving_Werking: Optional[str] = None
    Provinciaal_Belang: Optional[str] = None
    Aanleiding: Optional[str] = None
    Afweging: Optional[str] = None
    Besluitnummer: Optional[str] = None
    Tags: Optional[str] = None
    Status: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidskeuzeCreate(BeleidskeuzeBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidskeuzeUpdate(BeleidskeuzeBase):
    pass


class BeleidskeuzeInDBBase(BeleidskeuzeBase):
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Titel: str
    Omschrijving_Keuze: str
    Omschrijving_Werking: str
    Provinciaal_Belang: str
    Aanleiding: str
    Afweging: str
    Besluitnummer: Optional[str]
    Tags: Optional[str]
    Status: str
    Weblink: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


# Properties to return to client
class Beleidskeuze(BeleidskeuzeInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidsmodules: List[RelatedBeleidsmodule]
    Beleidsdoelen: List[RelatedBeleidsdoel]
    Maatregelen: List[RelatedMaatregel]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class BeleidskeuzeInDB(BeleidskeuzeInDBBase):
    pass


class BeleidskeuzeShortInline(BaseModel):
    ID: int
    UUID: str
    Titel: str

    class Config:
        orm_mode = True
