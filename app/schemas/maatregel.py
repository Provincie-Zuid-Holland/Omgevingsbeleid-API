from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict
from app.schemas.werkingsgebied import WerkingsgebiedShortInline

from app.util.legacy_helpers import to_ref_field

from .beleidskeuze import BeleidskeuzeShortInline
from .gebruiker import GebruikerInline

# Many to many schema's
class RelatedBeleidskeuzeGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidskeuze import BeleidskeuzeInDB

        keys = BeleidskeuzeInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Maatregel, key)
        else:
            return super(RelatedBeleidskeuzeGetter, self).get(key, default)


class RelatedBeleidskeuze(BeleidskeuzeShortInline):
    class Config:
        getter_dict = RelatedBeleidskeuzeGetter


class RelatedBeleidsmoduleGetter(GetterDict):
    def get(self, key: str, default: Any = None) -> Any:
        from .beleidsmodule import BeleidsmoduleInDB

        keys = BeleidsmoduleInDB.__fields__.keys()
        if key in keys:
            return getattr(self._obj.Maatregel, key)
        else:
            return super(RelatedBeleidsmoduleGetter, self).get(key, default)


class RelatedBeleidsmodule(BaseModel):
    ID: str
    UUID: str
    Titel: str
    Koppeling_Omschrijving: str

    class Config:
        orm_mode = True
        getter_dict = RelatedBeleidsmoduleGetter


# Shared properties
class MaatregelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Toelichting: Optional[str] = None
    Toelichting_Raw: Optional[str] = None
    Weblink: Optional[str] = None
    Status: Optional[str] = None
    Gebied_Duiding: Optional[str] = None
    Tags: Optional[str] = None


class MaatregelCreate(MaatregelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class MaatregelUpdate(MaatregelBase):
    pass


class MaatregelInDBBase(MaatregelBase):
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
    Toelichting: str
    Toelichting_Raw: str
    Weblink: str
    Status: str
    Gebied_Duiding: str
    Tags: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class AanpassingOp(BaseModel):
    UUID: str

    class Config:
        orm_mode = True



# Properties to return to client
class Maatregel(MaatregelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[RelatedBeleidskeuze]
    Beleidsmodules: List[RelatedBeleidsmodule]

    Eigenaar_1: GebruikerInline
    Eigenaar_2: GebruikerInline
    Portefeuillehouder_1: GebruikerInline
    Portefeuillehouder_2: GebruikerInline
    Gebied: WerkingsgebiedShortInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


# Properties properties stored in DB
class MaatregelInDB(MaatregelInDBBase):
    pass

