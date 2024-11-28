from pydantic import BaseModel, validator


class HierarchyStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    @validator("Cached_Title", pre=True)
    def default_empty_string(cls, v):
        return "" if v is None else v

    class Config:
        orm_mode = True
