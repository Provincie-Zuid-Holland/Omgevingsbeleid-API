from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class User(BaseModel):
    UUID: UUID
    Gebruikersnaam: str
    Email: str
    Rol: str
    Status: str
    IsActive: bool

    @field_validator("Email", mode="before")
    def default_empty_string(cls, v):
        return v or "<geen email>"

    model_config = ConfigDict(from_attributes=True)


class UserLoginDetail(BaseModel):
    UUID: UUID
    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    UUID: UUID
    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: Optional[str] = None
