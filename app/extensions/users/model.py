from typing import Optional
from uuid import UUID

from pydantic import BaseModel, validator


class User(BaseModel):
    UUID: UUID
    Gebruikersnaam: str
    Email: str
    Rol: str
    Status: str
    IsActive: bool

    @validator("Email", pre=True)
    def default_empty_string(cls, v):
        return v or "<geen email>"

    class Config:
        orm_mode = True


class UserLoginDetail(BaseModel):
    UUID: UUID
    Rol: str
    Gebruikersnaam: str

    class Config:
        orm_mode = True


class UserShort(BaseModel):
    UUID: UUID
    # Rol: str
    # Gebruikersnaam: str

    class Config:
        orm_mode = True


class TokenPayload(BaseModel):
    sub: Optional[str] = None
