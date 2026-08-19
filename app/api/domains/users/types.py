from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class TokenPayload(BaseModel):
    sub: str | None = None


class UserShort(BaseModel):
    UUID: UUID

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    UUID: UUID
    Gebruikersnaam: str
    Email: str
    Roles: list[str]
    Status: str
    IsActive: bool

    @field_validator("Email", mode="before")
    def default_empty_string(cls, v):
        return v or "<geen email>"

    model_config = ConfigDict(from_attributes=True)


class UserLoginDetail(BaseModel):
    UUID: UUID
    Roles: list[str]
    Gebruikersnaam: str

    model_config = ConfigDict(from_attributes=True)


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    identifier: UserLoginDetail

    model_config = ConfigDict(from_attributes=True)
