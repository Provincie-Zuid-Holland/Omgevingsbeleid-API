from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import GebruikerInline
from app.models.base import VerordeningstructuurStatus as StatusEnum

# TODO: structuur XML parse
class TreeNode(BaseModel):
    """
    Recursief schema voor boomstructuur
    """

    UUID: str
    Children: Optional[List["TreeNode"]] = None
    Titel: Optional[str] = ""
    Volgnummer: Optional[str] = None
    Type: str
    Inhoud: str
    Gebied: Optional[str] = None

    class Config:
        orm_mode = True


class TreeRoot(BaseModel):
    """
    Startpunt voor boomstructuur
    """

    Children: Optional[List[TreeNode]] = None

    class Config:
        orm_mode = True


class VerordeningstructuurBase(BaseModel):
    Titel: str
    Structuur: str
    Status: Optional[StatusEnum]


class VerordeningstructuurCreate(VerordeningstructuurBase):
    Begin_Geldigheid: datetime
    Eind_Geldigheid: datetime


class VerordeningstructuurUpdate(VerordeningstructuurCreate):
    Begin_Geldigheid: Optional[datetime]
    Eind_Geldigheid: Optional[datetime]

    Titel: Optional[str]
    Structuur: Optional[str]


class VerordeningstructuurInDBBase(VerordeningstructuurBase):
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


class VerordeningstructuurInDB(VerordeningstructuurInDBBase):
    pass


class Verordeningstructuur(VerordeningstructuurInDBBase):
    Created_By: GebruikerInline
    Modified_By: GebruikerInline
