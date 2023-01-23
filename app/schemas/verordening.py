from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic.utils import GetterDict

from app.schemas.common import (
    BeleidskeuzeReference,
    BeleidskeuzeShortInline,
    GebruikerInline,
    valid_ref_alias,
)

from .beleidskeuze import BeleidskeuzeInDB
from .werkingsgebied import WerkingsgebiedShortInline

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
class VerordeningBase(BaseModel):
    Type: str
    Status: str
    Volgnummer: str 

    Titel: Optional[str] = None
    Inhoud: Optional[str] = None
    Weblink: Optional[str] = None


class VerordeningCreate(VerordeningBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Portefeuillehouder_1_UUID: Optional[str]
    Portefeuillehouder_2_UUID: Optional[str]
    Eigenaar_1_UUID: Optional[str]
    Eigenaar_2_UUID: Optional[str]

    Opdrachtgever_UUID: Optional[str] = None
    Gebied_UUID: Optional[str] = None


class VerordeningUpdate(VerordeningCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Type: Optional[str] = None
    Volgnummer: Optional[str] = None
    Status: Optional[str] = None


class VerordeningInDBBase(VerordeningBase):
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
class Verordening(VerordeningInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Portefeuillehouder_1: GebruikerInline
    Portefeuillehouder_2: GebruikerInline
    Eigenaar_1: GebruikerInline
    Eigenaar_2: GebruikerInline
    Opdrachtgever: GebruikerInline
    Gebied: WerkingsgebiedShortInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias


class VerordeningInDB(VerordeningInDBBase):
    pass
