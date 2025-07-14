import uuid
from abc import ABCMeta
from datetime import datetime, timezone
from typing import List, Optional, Type

from pydantic import BaseModel, Field


class Column(BaseModel):
    id: str
    name: str
    type: str
    type_data: dict = {}
    nullable: bool = False
    static: bool = False
    serializers: List[str] = Field(default_factory=list)
    deserializers: List[str] = Field(default_factory=list)


class Model(BaseModel, metaclass=ABCMeta):
    id: str
    name: str
    pydantic_model: Type[BaseModel]


class DynamicObjectModel(Model):
    service_config: dict
    columns: List[Column]


class AcknowledgedRelationBase(BaseModel):
    Object_ID: int
    Object_Type: str
    Explanation: Optional[str] = Field(None)

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    Acknowledged: Optional[datetime] = None
    Acknowledged_By_UUID: Optional[uuid.UUID] = None
    Title: Optional[str] = None
    Explanation: Optional[str] = None

    @property
    def Is_Acknowledged(self) -> bool:
        return self.Acknowledged is not None

    @property
    def Acknowledged_Date(self) -> datetime:
        return self.Acknowledged

    def disapprove(self):
        self.Acknowledged = None

    def approve(self, user_uuid: uuid.UUID, timepoint: Optional[datetime] = None):
        timepoint = timepoint or datetime.now(timezone.utc)
        if self.Is_Acknowledged:
            return

        self.Acknowledged_By_UUID = user_uuid
        self.Acknowledged = timepoint


class WerkingsgebiedRelatedObjectShort(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Title: Optional[str]
    Werkingsgebied_Code: str


class WerkingsgebiedRelatedModuleObjectShort(WerkingsgebiedRelatedObjectShort):
    Module_ID: Optional[int] = None
    Module_Title: Optional[str] = None


class WerkingsgebiedRelatedObjects(BaseModel):
    Valid_Objects: List[WerkingsgebiedRelatedObjectShort]
    Module_Objects: List[WerkingsgebiedRelatedModuleObjectShort]
