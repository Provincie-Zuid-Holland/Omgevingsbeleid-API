from enum import Enum
import uuid
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator

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
    Start_Validity: Optional[datetime] = Field(None, nullable=True)
    End_Validity: Optional[datetime] = Field(None, nullable=True)
    Status: Optional[ModuleStatus]

    Created_By: Optional[UserShort]
    Modified_By: Optional[UserShort]
    Module_Manager_1: Optional[UserShort]
    Module_Manager_2: Optional[UserShort]

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
    Vigerend = "Vigerend"


class AllModuleStatusCode(str, Enum):
    Niet_Actief = "Niet-Actief"
    Ontwerp_GS_Concept = "Ontwerp GS Concept"
    Ontwerp_GS = "Ontwerp GS"
    Definitief_Ontwerp_GS = "Definitief ontwerp GS"
    Ontwerp_PS_Concept = "Ontwerp PS Concept"
    Ontwerp_PS = "Ontwerp PS"
    Definitief_Ontwerp_PS = "Definitief ontwerp PS"
    Vigerend = "Vigerend"


class ModulePatchStatus(BaseModel):
    Status: ModuleStatusCode

    class Config:
        use_enum_values = True


class ModuleObjectContextShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str

    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Action: str

    class Config:
        orm_mode = True


class ModuleObjectContext(ModuleObjectContextShort):
    Explanation: str
    Conclusion: str


class ModuleObjectAction(str, Enum):
    Edit = "Edit"
    Terminate = "Terminate"


class ModuleObjectShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str
    UUID: uuid.UUID

    Modified_Date: datetime

    Title: str
    Owner_1_UUID: Optional[uuid.UUID]
    Owner_2_UUID: Optional[uuid.UUID]

    # From Context
    Action: str
    Original_Adjust_On: Optional[uuid.UUID]


class ModuleSnapshot(BaseModel):
    Objects: List[dict]
