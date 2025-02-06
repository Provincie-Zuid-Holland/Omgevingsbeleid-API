import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.extensions.users.model import UserShort


class ModuleStatus(BaseModel):
    ID: int
    Module_ID: int
    Status: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


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
    Module_Manager_2_UUID: Optional[uuid.UUID] = None
    Status: Optional[ModuleStatus] = None

    Created_By: Optional[UserShort] = None
    Modified_By: Optional[UserShort] = None
    Module_Manager_1: Optional[UserShort] = None
    Module_Manager_2: Optional[UserShort] = None
    model_config = ConfigDict(from_attributes=True)


class ModuleShort(BaseModel):
    Module_ID: int
    Closed: bool
    Title: str
    Description: str
    Status: Optional[ModuleStatus] = None
    Module_Manager_1: Optional[UserShort] = None
    Module_Manager_2: Optional[UserShort] = None
    model_config = ConfigDict(from_attributes=True)


class ActiveModuleObject(BaseModel):
    Module_ID: Optional[int] = None
    UUID: uuid.UUID
    Modified_Date: datetime
    Title: str
    model_config = ConfigDict(from_attributes=True)


# @note: Existing but removed status codes
# Ontwerp_PS_Concept = "Ontwerp PS Concept"
class ModuleStatusCode(str, Enum):
    Ontwerp_GS_Concept = "Ontwerp GS Concept"
    Ontwerp_GS = "Ontwerp GS"
    Ontwerp_PS = "Ontwerp PS"
    Ter_Inzage = "Ter Inzage"
    Definitief_Ontwerp_GS_Concept = "Definitief ontwerp GS Concept"
    Definitief_Ontwerp_GS = "Definitief ontwerp GS"
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


class ModuleStatusCodeInternal(str, Enum):
    Niet_Actief = "Niet-Actief"
    Gesloten = "Gesloten"
    Module_afgerond = "Module afgerond"


class ModulePatchStatus(BaseModel):
    Status: ModuleStatusCode
    model_config = ConfigDict(use_enum_values=True)


class ModuleObjectAction(str, Enum):
    Edit = "Edit"
    Terminate = "Terminate"


class ModuleObjectActionFull(str, Enum):
    Create = "Create"
    Edit = "Edit"
    Terminate = "Terminate"


class ModuleSnapshot(BaseModel):
    Objects: List[dict]


class PublicModuleShort(BaseModel):
    Module_ID: int
    Title: str
    Description: str
    Status: Optional[ModuleStatus] = None

    @field_validator("Title", "Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True)


class PublicModuleStatusCode(str, Enum):
    Ter_Inzage = ModuleStatusCode.Ter_Inzage.value
    Ontwerp_GS = ModuleStatusCode.Ontwerp_GS.value
    Definitief_Ontwerp_GS = ModuleStatusCode.Definitief_Ontwerp_GS.value
    Ontwerp_PS = ModuleStatusCode.Ontwerp_PS.value
    Definitief_Ontwerp_PS = ModuleStatusCode.Definitief_Ontwerp_PS.value
    Vastgesteld = ModuleStatusCode.Vastgesteld.value

    @staticmethod
    def values():
        return [status.value for status in PublicModuleStatusCode]


class PublicModuleObjectRevision(BaseModel):
    Module_Object_UUID: uuid.UUID
    Module_ID: int
    Module_Title: str
    Module_Status: str
    Action: ModuleObjectActionFull


class GenericModuleObjectShort(BaseModel):
    UUID: uuid.UUID
    Object_ID: int
    Object_Type: str
    Title: str
    Module_ID: Optional[int] = None
    Module_Title: Optional[str] = None
