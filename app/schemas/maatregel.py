from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, BeleidskeuzeReference
from app.schemas.werkingsgebied import WerkingsgebiedShortInline


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


class MaatregelUpdate(MaatregelCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class MaatregelInDBBase(MaatregelBase):
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


def reference_alias_generator(field: str) -> str:
    """
    Hack to enable manual aliassing of schema output which
    is not yet supported in FastApi
    """
    aliasses = {
        "Beleidskeuzes": "Ref_Beleidskeuzes",
        "Beleidsmodules": "Ref_Beleidsmodules",
    }

    if field in aliasses:
        return aliasses[field]

    return field


class Maatregel(MaatregelInDBBase):
    """
    Full Maatregel object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[BeleidskeuzeReference]
    Beleidsmodules: List[BeleidskeuzeReference]

    Eigenaar_1: GebruikerInline
    Eigenaar_2: GebruikerInline
    Portefeuillehouder_1: GebruikerInline
    Portefeuillehouder_2: GebruikerInline
    Gebied: WerkingsgebiedShortInline

    class Config:
        allow_population_by_field_name = True
        alias_generator = reference_alias_generator


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

    Status: str
    Titel: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class MaatregelInDB(MaatregelInDBBase):
    pass
