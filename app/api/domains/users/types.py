from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class TokenPayload(BaseModel):
    sub: str | None = None


class UserShort(BaseModel):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: UUID
    name: str
    email: str
    roles: list[str]
    is_active: bool

    @field_validator("email", mode="before")
    def default_empty_string(cls, v):
        return v or "<geen email>"

    model_config = ConfigDict(from_attributes=True)


class UserLoginDetail(BaseModel):
    id: UUID
    roles: list[str]
    name: str

    model_config = ConfigDict(from_attributes=True)


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    identifier: UserLoginDetail

    model_config = ConfigDict(from_attributes=True)
