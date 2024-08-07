from typing import Dict

from pydantic import BaseModel, BaseSettings


class RenvooiSettings(BaseModel):
    DSO_API_KEY: str
    RENVOOI_API_KEY: str


class PublicationSettings(BaseSettings):
    PUBLICATION_RENVOOI: Dict[str, RenvooiSettings]
