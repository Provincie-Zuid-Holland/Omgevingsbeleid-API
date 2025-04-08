from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserShort(BaseModel):
    UUID: UUID

    model_config = ConfigDict(from_attributes=True)


class UserLoginDetail(BaseModel):
    UUID: UUID
    Rol: str
    Gebruikersnaam: str

    model_config = ConfigDict(from_attributes=True)
