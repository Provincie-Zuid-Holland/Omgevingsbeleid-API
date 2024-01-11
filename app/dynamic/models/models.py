from pydantic import BaseModel


class ObjectCount(BaseModel):
    Object_Type: str
    Count: int

    class Config:
        orm_mode = True
