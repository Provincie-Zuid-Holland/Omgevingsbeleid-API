from typing import Optional

from pydantic import BaseModel


# Shared properties
class AmbitieBase(BaseModel):
    Titel: Optional[str] = None
    Omschrijving: Optional[str] = None
    Weblink: Optional[str] = None


class AmbitieCreate(AmbitieBase):
    pass


class AmbitieUpdate(AmbitieBase):
    pass


class AmbitieInDBBase(AmbitieBase):
    ID: int
    Titel: str

    class Config:
        orm_mode = True


# Properties to return to client
class Ambitie(AmbitieInDBBase):
    pass


# Properties properties stored in DB
class AmbitieInDB(AmbitieInDBBase):
    pass
