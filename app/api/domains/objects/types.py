from pydantic import BaseModel, ConfigDict


class ObjectCount(BaseModel):
    object_type: str
    count: int

    model_config = ConfigDict(from_attributes=True)
