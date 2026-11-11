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
    object_id: int
    object_type: str
    explanation: str | None = Field(None)

    @property
    def code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class AcknowledgedRelationSide(AcknowledgedRelationBase):
    acknowledged: datetime | None = None
    acknowledged_by_id: uuid.UUID | None = None
    title: str | None = None
    explanation: str | None = None

    @property
    def is_acknowledged(self) -> bool:
        return self.acknowledged is not None

    @property
    def acknowledged_date(self) -> datetime:
        return self.acknowledged

    def disapprove(self):
        self.acknowledged = None

    def approve(self, user_uuid: uuid.UUID, timepoint: datetime | None = None):
        timepoint = timepoint or datetime.now(UTC)
        if self.is_acknowledged:
            return

        self.acknowledged_by_id = user_uuid
        self.acknowledged = timepoint


class WerkingsgebiedRelatedObjectShort(BaseModel):
    id: uuid.UUID
    object_type: str
    object_id: int
    title: str | None
    werkingsgebied_code: str


class WerkingsgebiedRelatedModuleObjectShort(WerkingsgebiedRelatedObjectShort):
    module_id: int | None = None
    module_title: str | None = None


class WerkingsgebiedRelatedObjects(BaseModel):
    valid_objects: list[WerkingsgebiedRelatedObjectShort]
    module_objects: list[WerkingsgebiedRelatedModuleObjectShort]
