from enum import Enum
import uuid
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from app.extensions.users.model import UserShort


class ModuleStatus(BaseModel):
    ID: int
    Module_ID: int
    Status: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID

    class Config:
        orm_mode = True


class Module(BaseModel):
    Module_ID: int
    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID
    Activated: bool
    Closed: bool
    Successful: bool
    Temporary_Locked: bool
    Title: str
    Description: str
    Module_Manager_1_UUID: uuid.UUID
    Module_Manager_2_UUID: Optional[uuid.UUID] = Field(None, nullable=True)
    Status: Optional[ModuleStatus]

    Created_By: Optional[UserShort]
    Modified_By: Optional[UserShort]
    Module_Manager_1: Optional[UserShort]
    Module_Manager_2: Optional[UserShort]

    class Config:
        orm_mode = True


class ActiveModuleObject(BaseModel):
    Module_ID: int
    UUID: uuid.UUID
    Modified_Date: datetime
    Title: str

    class Config:
        orm_mode = True


class ModuleStatusCode(str, Enum):
    Niet_Actief = "Niet-Actief"
    Ontwerp_GS_Concept = "Ontwerp GS Concept"
    Ontwerp_GS = "Ontwerp GS"
    Definitief_Ontwerp_GS = "Definitief ontwerp GS"
    Ontwerp_PS_Concept = "Ontwerp PS Concept"
    Ontwerp_PS = "Ontwerp PS"
    Definitief_Ontwerp_PS = "Definitief ontwerp PS"
    Vastgesteld = "Vastgesteld"

    @staticmethod
    def after(status):
        # Return a list of statuses that are
        # after the given status in the order of the enum
        statuses = list(ModuleStatusCode)
        index = next((i for i, s in enumerate(statuses) if s.value == status), None)
        if index is not None:
            result = [status.value for status in statuses[index:]]
            return result
        else:
            raise ValueError(f"Invalid status: {status}")

    @staticmethod
    def values():
        return [status.value for status in ModuleStatusCode]


class ModulePatchStatus(BaseModel):
    Status: ModuleStatusCode

    class Config:
        use_enum_values = True


class ModuleObjectAction(str, Enum):
    Edit = "Edit"
    Terminate = "Terminate"


class ModuleSnapshot(BaseModel):
    Objects: List[dict]


class Statics(BaseModel):
    # TODO: Make compatitble with dynamic config
    Owner_1_UUID: Optional[uuid.UUID]
    Owner_2_UUID: Optional[uuid.UUID]
    Portfolio_Holder_1_UUID: Optional[uuid.UUID]
    Portfolio_Holder_2_UUID: Optional[uuid.UUID]
    Client_1_UUID: Optional[uuid.UUID]

    class Config:
        orm_mode = True


class SearchObject(BaseModel):
    Object_Type: str
    Object_ID: int
    UUID: uuid.UUID
    Title: str
    Description: str


class ModuleSearchObject(SearchObject):
    Module_ID: Optional[int]


class SearchResult(BaseModel):
    Statics: Optional[Statics]
    Valid: Optional[SearchObject]
    Modules: List[ModuleSearchObject] = []


class AllObjectsResponse(BaseModel):
    Total: int = 0
    Results: List[SearchResult] = []
