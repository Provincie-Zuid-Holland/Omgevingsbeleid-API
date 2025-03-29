import uuid
from typing import List, Optional

from pydantic import BaseModel


class DynamicObjectShort(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Title: Optional[str]


class DynamicModuleObjectShort(DynamicObjectShort):
    Module_ID: Optional[int] = None
    Module_Title: Optional[str] = None


class WerkingsgebiedRelatedObjects(BaseModel):
    Valid_Objects: List[DynamicObjectShort]
    Module_Objects: List[DynamicModuleObjectShort]
