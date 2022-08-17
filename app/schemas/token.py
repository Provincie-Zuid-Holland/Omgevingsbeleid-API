from typing import Optional

from pydantic import BaseModel

from .relationships import GebruikerInline


class Token(BaseModel):
    access_token: str
    token_type: str
    identifier: GebruikerInline


class TokenPayload(BaseModel):
    sub: Optional[str] = None
