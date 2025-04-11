from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class UserShort(BaseModel):
    UUID: UUID

    model_config = ConfigDict(from_attributes=True)


class UserLoginDetail(BaseModel):
    UUID: UUID
    Rol: str
    Gebruikersnaam: str

    model_config = ConfigDict(from_attributes=True)


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    identifier: UserLoginDetail

    model_config = ConfigDict(from_attributes=True)
