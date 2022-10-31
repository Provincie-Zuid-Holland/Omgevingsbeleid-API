from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.schemas.common import (
    BeleidsmoduleReference,
    BeleidskeuzeShortInline,
    GebruikerInline,
    RelatedAmbitie,
    RelatedBelang,
    RelatedBeleidsdoel,
    RelatedBeleidsprestatie,
    RelatedBeleidsregel,
    RelatedMaatregel,
    RelatedThema,
    RelatedVerordeningen,
    RelatedWerkingsgebied,
)


def reference_alias_generator(field: str) -> str:
    """
    Hack to enable manual aliassing of schema output which
    is not yet supported in FastApi
    """
    aliasses = {
        "Beleidsmodules": "Ref_Beleidsmodules",
    }

    if field in aliasses:
        return aliasses[field]

    return field


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


class BeleidskeuzeUpdate(BeleidskeuzeCreate):
    pass


class BeleidskeuzeInDBBase(BeleidskeuzeBase):
    """
    Base beleidskeuze schema mirroring ORM model. Raw foreign keys.
    """
    ID: int
    UUID: str

    Created_By: str
    Created_Date: datetime
    Modified_By: str
    Modified_Date: datetime
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Eigenaar_1: Optional[str]
    Eigenaar_2: Optional[str]
    Portefeuillehouder_1: Optional[str]
    Portefeuillehouder_2: Optional[str]

    Opdrachtgever: Optional[str]
    Aanpassing_Op: Optional[str]

    class Config:
        orm_mode = True


class BeleidskeuzeInDB(BeleidskeuzeInDBBase):
    pass


class Beleidskeuze(BeleidskeuzeInDB):
    """
    Full beleidskeuze object schema with serialized 
    many to many relationships.

    TODO: cannot alias aanpassing_op, self reference conflict orm model
    """

    # User serializers
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Eigenaar_1: Optional[GebruikerInline]
    Eigenaar_2: Optional[GebruikerInline]
    Portefeuillehouder_1: Optional[GebruikerInline]
    Portefeuillehouder_2: Optional[GebruikerInline]

    # Relation serializers
    Aanpassing_Op: Optional[Any]
    Ambities: List[RelatedAmbitie]
    Belangen: List[RelatedBelang]
    Beleidsprestaties: List[RelatedBeleidsprestatie]
    Beleidsregels: List[RelatedBeleidsregel]
    Themas: List[RelatedThema]
    Verordeningen: List[RelatedVerordeningen]
    Werkingsgebieden: List[RelatedWerkingsgebied]
    Beleidsdoelen: List[RelatedBeleidsdoel]
    Maatregelen: List[RelatedMaatregel]
    #Beleidsrelaties

    # Refs
    Beleidsmodules: List[BeleidsmoduleReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = reference_alias_generator



class BeleidskeuzeListable(BeleidskeuzeShortInline):
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

    Beleidsmodules: List[BeleidsmoduleReference]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        alias_generator = reference_alias_generator

