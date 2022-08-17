from pydantic import BaseModel as PydanticBase

from app.util.legacy_helpers import DEFAULT_SEARCH_FIELDS

class BaseModel(PydanticBase):
    class Config:
        searchable = True
        search_fields = DEFAULT_SEARCH_FIELDS
