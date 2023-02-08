from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.base import UserStatus


class GebruikerBase(BaseModel):
    Gebruikersnaam: Optional[str] = None
    Rol: Optional[str] = None
    Email: Optional[EmailStr] = None
    Status: Optional[UserStatus] = None


class GebruikerCreate(GebruikerBase):
    Email: EmailStr
    Wachtwoord: str


class GebruikerUpdate(GebruikerBase):
    Wachtwoord: Optional[str] = None


class PasswordUpdate(BaseModel):
    password: str
    new_password: str


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
