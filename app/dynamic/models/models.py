from pydantic import BaseModel, ConfigDict


class ObjectCount(BaseModel):
    Object_Type: str
    Count: int
    model_config = ConfigDict(from_attributes=True)
