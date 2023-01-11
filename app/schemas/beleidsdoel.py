from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline, BeleidskeuzeReference, RelatedAmbitie
from app.util.legacy_helpers import valid_ref_alias


class BeleidsdoelBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class BeleidsdoelCreate(BeleidsdoelBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class BeleidsdoelUpdate(BeleidsdoelCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]


class BeleidsdoelInDBBase(BeleidsdoelBase):
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


class BeleidsdoelInDB(BeleidsdoelInDBBase):
    pass


class Beleidsdoel(BeleidsdoelInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline

    # Relations
    Ambities: List[RelatedAmbitie]

    # Reverse refs
    Valid_Beleidskeuzes: List[BeleidskeuzeReference]

    class Config:
        allow_population_by_field_name = True
        alias_generator = valid_ref_alias
