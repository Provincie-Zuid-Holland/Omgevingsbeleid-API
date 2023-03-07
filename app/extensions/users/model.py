from typing import Optional
from uuid import UUID

import pydantic


class User(pydantic.BaseModel):
    UUID: UUID
    Gebruikersnaam: str
    Email: str
    Rol: str
    IsActief: bool

    class Config:
        orm_mode = True


# class Token(BaseModel):
#     access_token: str
#     token_type: str
#     identifier: User


class TokenPayload(pydantic.BaseModel):
    sub: Optional[str] = None
