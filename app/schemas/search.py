from typing import Optional, Union, List
from pydantic import BaseModel


class SearchResult(BaseModel):
    Omschrijving: Optional[str]
    Type: str
    RANK: int
    UUID: str


class GeoSearchResult(BaseModel):
    Gebied: str
    Titel: str
    Omschrijving: str
    Type: str
    UUID: str
    RANK: int = 100


class SearchResultWrapper(BaseModel):
    results: List[Union[GeoSearchResult, SearchResult]] = []
    total: int = 0
