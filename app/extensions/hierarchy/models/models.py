from pydantic import BaseModel, ConfigDict, field_validator


class HierarchyStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @field_validator("Cached_Title", mode="before")
    @classmethod
    def default_empty_string(cls, v):
        return "" if v is None else v

    model_config = ConfigDict(from_attributes=True)
