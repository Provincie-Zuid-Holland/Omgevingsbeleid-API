from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class GebruikerBase(BaseModel):
    Gebruikersnaam: Optional[str] = None
    Rol: Optional[str] = None
    Email: Optional[EmailStr] = None
    Status: Optional[str] = None


class GebruikerCreate(GebruikerBase):
    Email: EmailStr
    Wachtwoord: str


class GebruikerUpdate(GebruikerBase):
    Wachtwoord: Optional[str] = None


class GebruikerInDBBase(GebruikerBase):
    ID: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Gebruiker(GebruikerInDBBase):
    pass


# Additional properties stored in DB
class GebruikerInDB(GebruikerInDBBase):
    Wachtwoord: str


# Joined classes

class GebruikerInline(BaseModel):
    Gebruikersnaam: str
    Rol: str
    Status: str
    UUID: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
