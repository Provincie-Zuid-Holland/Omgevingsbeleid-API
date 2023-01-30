from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.base import Status as StatusEnum
from app.schemas.common import GebruikerInline, strip_UUID, valid_ref_alias
from app.schemas.reference import BeleidskeuzeReference
from app.schemas.werkingsgebied import WerkingsgebiedShortInline

class MaatregelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Toelichting: Optional[str] = None
    Toelichting_Raw: Optional[str] = None
    Weblink: Optional[str] = None
    Status: Optional[StatusEnum] = None
    Gebied_Duiding: Optional[str] = None
    Tags: Optional[str] = None


class MaatregelCreate(MaatregelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Eigenaar_1_UUID: Optional[str]
    Eigenaar_2_UUID: Optional[str]
    Portefeuillehouder_1_UUID: Optional[str]
    Portefeuillehouder_2_UUID: Optional[str]
    Opdrachtgever_UUID: Optional[str]
    Gebied_UUID: Optional[str]


class MaatregelUpdate(MaatregelCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Aanpassing_Op: Optional[str]


class MaatregelInDBBase(MaatregelBase):
    ID: int
    UUID: str

    Created_Date: datetime
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime
    Aanpassing_Op: Optional[str]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class MaatregelInDB(MaatregelInDBBase):
    Created_By: str
    Modified_By: str


class MaatregelInline(MaatregelInDBBase):
    Created_By_UUID: str
    Modified_By_UUID: str

    class Config:
        allow_population_by_field_name = True
        alias_generator = strip_UUID


class Maatregel(MaatregelInDBBase):
    """
    Full Maatregel object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Valid_Beleidskeuzes: List[BeleidskeuzeReference]
    Beleidsmodules: List[BeleidskeuzeReference]

    Eigenaar_1: GebruikerInline
    Eigenaar_2: GebruikerInline
    Portefeuillehouder_1: GebruikerInline
    Portefeuillehouder_2: GebruikerInline
    Opdrachtgever: GebruikerInline
    Gebied: WerkingsgebiedShortInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias


class MaatregelListable(BaseModel):
    """
    Schema containing bare crud details and descriptions
    for usage in list views.
    """

    ID: int
    UUID: str

    Created_By: GebruikerInline
    Created_Date: datetime
    Modified_By: GebruikerInline
    Modified_Date: datetime

    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Status: StatusEnum
    Titel: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
