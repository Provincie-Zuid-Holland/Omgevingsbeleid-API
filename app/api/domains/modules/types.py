import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

from app.api.domains.users.types import UserShort


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


class ModuleObjectAction(str, Enum):
    Edit = "Edit"
    Terminate = "Terminate"


class ModuleObjectActionFull(str, Enum):
    Create = "Create"
    Edit = "Edit"
    Terminate = "Terminate"


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
    Module_ID: int
    Module_Title: str
    Module_Status: ModuleStatusCode
    Module_Object_UUID: uuid.UUID
    Module_Object_Code: str
    Module_Object_Status: PublicModuleStatusCode
    Action: ModuleObjectActionFull

    model_config = ConfigDict(from_attributes=True)


class ModuleStatus(BaseModel):
    ID: int
    Module_ID: int
    Status: str
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class ModuleShort(BaseModel):
    Module_ID: int
    Closed: bool
    Title: str
    Description: str
    Status: ModuleStatus | None = None
    Module_Manager_1: UserShort | None = None
    Module_Manager_2: UserShort | None = None
    model_config = ConfigDict(from_attributes=True)


class ActiveModuleObject(BaseModel):
    Module_ID: int | None = None
    UUID: uuid.UUID
    Modified_Date: datetime
    Title: str
    model_config = ConfigDict(from_attributes=True)


class ObjectStaticShort(BaseModel):
    Owner_1_UUID: uuid.UUID | None = None
    Owner_2_UUID: uuid.UUID | None = None
    Portfolio_Holder_1_UUID: uuid.UUID | None = None
    Portfolio_Holder_2_UUID: uuid.UUID | None = None
    Client_1_UUID: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class ModuleObjectContextShort(BaseModel):
    Action: str
    Original_Adjust_On: uuid.UUID | None = None
    model_config = ConfigDict(from_attributes=True)


class ModuleObjectShort(BaseModel):
    Module_ID: int
    Object_Type: str
    Object_ID: int
    Code: str
    UUID: uuid.UUID

    Modified_Date: datetime
    Title: str

    ObjectStatics: ObjectStaticShort | None = None
    ModuleObjectContext: ModuleObjectContextShort | None = None
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
    Module_Manager_2_UUID: uuid.UUID | None = None
    Status: ModuleStatus | None = None

    Created_By: UserShort | None = None
    Modified_By: UserShort | None = None
    Module_Manager_1: UserShort | None = None
    Module_Manager_2: UserShort | None = None
    model_config = ConfigDict(from_attributes=True)


class PublicModuleShort(BaseModel):
    Module_ID: int
    Title: str
    Description: str
    Status: ModuleStatus | None = None

    @field_validator("Title", "Description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True)


class ModuleSortColumn(str, Enum):
    Module_ID = "Module_ID"
    Title = "Title"
    Created_Date = "Created_Date"
    Modified_Date = "Modified_Date"
    Activated = "Activated"
    Closed = "Closed"
    Successful = "Successful"
    Temporary_Locked = "Temporary_Locked"


class GenericObjectShort(BaseModel):
    Object_Type: str
    Object_ID: int
    UUID: uuid.UUID
    Title: str | None = None
    model_config = ConfigDict(from_attributes=True)
