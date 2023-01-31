from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.base import Status as StatusEnum
from app.schemas.common import GebruikerInline, to_ref_field
from app.schemas.reference import BeleidsmoduleReference, GenericReferenceUpdate
from app.schemas.related import (
    RelatedBelang,
    RelatedBeleidsdoel,
    RelatedBeleidsprestatie,
    RelatedBeleidsregel,
    RelatedMaatregel,
    RelatedThema,
    RelatedVerordeningen,
    RelatedWerkingsgebied,
)

### Beleidskeuze Schemas ###


class BeleidskeuzeBase(BaseModel):
    Status: StatusEnum
    Titel: str
    Omschrijving_Keuze: Optional[str] = None
    Omschrijving_Werking: Optional[str] = None
    Provinciaal_Belang: Optional[str] = None
    Aanleiding: Optional[str] = None
    Afweging: Optional[str] = None
    Besluitnummer: Optional[str] = None
    Tags: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidskeuzeCreate(BeleidskeuzeBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime

    Eigenaar_1_UUID: Optional[str]
    Eigenaar_2_UUID: Optional[str]
    Portefeuillehouder_1_UUID: Optional[str]
    Portefeuillehouder_2_UUID: Optional[str]
    Opdrachtgever_UUID: Optional[str]

    Belangen: Optional[List[GenericReferenceUpdate]] = []
    Beleidsprestaties: Optional[List[GenericReferenceUpdate]] = []
    Beleidsregels: Optional[List[GenericReferenceUpdate]] = []
    Themas: Optional[List[GenericReferenceUpdate]] = []
    Verordeningen: Optional[List[GenericReferenceUpdate]] = []
    Werkingsgebieden: Optional[List[GenericReferenceUpdate]] = []
    Beleidsdoelen: Optional[List[GenericReferenceUpdate]] = []
    Maatregelen: Optional[List[GenericReferenceUpdate]] = []


class BeleidskeuzeUpdate(BeleidskeuzeCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Status: Optional[StatusEnum]
    Titel: Optional[str]

    Aanpassing_Op: Optional[str]


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
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Eigenaar_1: Optional[GebruikerInline]
    Eigenaar_2: Optional[GebruikerInline]
    Portefeuillehouder_1: Optional[GebruikerInline]
    Portefeuillehouder_2: Optional[GebruikerInline]
    Opdrachtgever: Optional[GebruikerInline]

    # Relation serializers
    Belangen: List[RelatedBelang]
    Beleidsprestaties: List[RelatedBeleidsprestatie]
    Beleidsregels: List[RelatedBeleidsregel]
    Themas: List[RelatedThema]
    Verordeningen: List[RelatedVerordeningen]
    Werkingsgebieden: List[RelatedWerkingsgebied]
    Beleidsdoelen: List[RelatedBeleidsdoel]
    Maatregelen: List[RelatedMaatregel]

    # Refs
    Beleidsmodules: List[BeleidsmoduleReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = to_ref_field


class BeleidskeuzeListable(BaseModel):
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

    Beleidsmodules: List[BeleidsmoduleReference]

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        alias_generator = to_ref_field
