from typing import Dict

from pydantic import BaseModel, BaseSettings, Field


class KoopSettings(BaseModel):
    API_KEY: str
    RENVOOI_API_URL: str
    PREVIEW_API_URL: str


class PublicationSettings(BaseSettings):
    PUBLICATION_KOOP: Dict[str, KoopSettings] = Field({})
