from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


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
    Rol: str
    Gebruikersnaam: str
    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    UUID: UUID
    Rol: str
    Gebruikersnaam: str

    @field_validator("Rol", "Gebruikersnaam", mode="after")
    def hide_data(cls, v: str, info: ValidationInfo) -> str:
        if not isinstance(info.context, dict):
            return ""
        if not info.context.get("user"):
            return ""
        return v

    model_config = ConfigDict(from_attributes=True)


class TokenPayload(BaseModel):
    sub: Optional[str] = None
