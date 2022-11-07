from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import BeleidskeuzeReference, GebruikerInline


class AmbitieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class AmbitieCreate(AmbitieBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class AmbitieUpdate(AmbitieBase):
    pass


class AmbitieInDBBase(AmbitieBase):
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


class AmbitieInDB(AmbitieInDBBase):
    pass


def reference_alias_generator(field: str) -> str:
    """
    Hack to enable manual aliassing of schema output which
    is not yet supported in FastApi
    """
    aliasses = {
        "Beleidskeuzes": "Ref_Beleidskeuzes",
    }

    if field in aliasses:
        return aliasses[field]

    return field


class Ambitie(AmbitieInDBBase):
    """
    Full Ambitie object schema with serialized
    many to many relationships.
    """

    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = reference_alias_generator
