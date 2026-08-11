import uuid
from abc import ABCMeta
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Column(BaseModel):
    id: str
    name: str
    type: str
    type_data: dict = {}
    nullable: bool = False
    static: bool = False
    serializers: list[str] = Field(default_factory=list)
    deserializers: list[str] = Field(default_factory=list)


class Model(BaseModel, metaclass=ABCMeta):
    id: str
    name: str
    pydantic_model: type[BaseModel]


class DynamicObjectModel(Model):
    service_config: dict
    columns: list[Column]


class AcknowledgedRelationBase(BaseModel):
    Object_ID: int
    Object_Type: str
    Explanation: str | None = Field(None)

    @property
    def Code(self) -> str:
        return f"{self.Object_Type}-{self.Object_ID}"


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    Acknowledged: datetime | None = None
    Acknowledged_By_UUID: uuid.UUID | None = None
    Title: str | None = None
    Explanation: str | None = None

    @property
    def Is_Acknowledged(self) -> bool:
        return self.Acknowledged is not None

    @property
    def Acknowledged_Date(self) -> datetime:
        return self.Acknowledged

    def disapprove(self):
        self.Acknowledged = None

    def approve(self, user_uuid: uuid.UUID, timepoint: datetime | None = None):
        timepoint = timepoint or datetime.now(UTC)
        if self.Is_Acknowledged:
            return

        self.Acknowledged_By_UUID = user_uuid
        self.Acknowledged = timepoint


class WerkingsgebiedRelatedObjectShort(BaseModel):
    UUID: uuid.UUID
    Object_Type: str
    Object_ID: int
    Title: str | None
    Werkingsgebied_Code: str


class WerkingsgebiedRelatedModuleObjectShort(WerkingsgebiedRelatedObjectShort):
    Module_ID: int | None = None
    Module_Title: str | None = None


class WerkingsgebiedRelatedObjects(BaseModel):
    Valid_Objects: list[WerkingsgebiedRelatedObjectShort]
    Module_Objects: list[WerkingsgebiedRelatedModuleObjectShort]
