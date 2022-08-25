from typing import Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    Omschrijving: Optional[str]
    Type: str
    RANK: int
    UUID: str
