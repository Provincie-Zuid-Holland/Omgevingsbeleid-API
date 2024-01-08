from pydantic import BaseModel


class HierarchyStatics(BaseModel):
    Object_Type: str
    Object_ID: int
    Code: str
    Cached_Title: str

    class Config:
        orm_mode = True
