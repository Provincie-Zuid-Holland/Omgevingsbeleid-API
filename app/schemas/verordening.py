from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.base import Status as StatusEnum
from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference

from .werkingsgebied import WerkingsgebiedShortInline

class VerordeningBase(BaseModel):
    Type: str
    Status: StatusEnum
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

    Type: Optional[str]
    Volgnummer: Optional[str]
    Status: Optional[StatusEnum]


class VerordeningInDBBase(VerordeningBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class VerordeningInDB(VerordeningInDBBase):
    Created_By: str
    Modified_By: str


class VerordeningInline(VerordeningInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


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
