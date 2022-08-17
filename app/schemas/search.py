from pydantic import BaseModel


class SearchResult(BaseModel):
    Omschrijving: str
    Type: str
    RANK: int
    UUID: str
