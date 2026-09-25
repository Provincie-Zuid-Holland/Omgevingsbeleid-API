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
    module_id: int
    module_title: str
    module_status: ModuleStatusCode
    module_object_id: uuid.UUID
    module_object_code: str
    module_object_status: PublicModuleStatusCode
    action: ModuleObjectActionFull

    model_config = ConfigDict(from_attributes=True)


class ModuleStatus(BaseModel):
    id: int
    module_id: int
    status: str
    created_date: datetime
    created_by_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ModuleShort(BaseModel):
    module_id: int
    closed: bool
    title: str
    description: str
    status: ModuleStatus | None = None
    module_manager_1: UserShort | None = None
    module_manager_2: UserShort | None = None

    model_config = ConfigDict(from_attributes=True)


class ActiveModuleObject(BaseModel):
    module_id: int | None = None
    id: uuid.UUID
    modified_date: datetime
    title: str

    model_config = ConfigDict(from_attributes=True)


class ObjectStaticShort(BaseModel):
    owner_1_id: uuid.UUID | None = None
    owner_2_id: uuid.UUID | None = None
    portfolio_holder_1_id: uuid.UUID | None = None
    portfolio_holder_2_id: uuid.UUID | None = None
    client_1_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ModuleObjectContextShort(BaseModel):
    action: str
    original_adjust_on: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ModuleObjectShort(BaseModel):
    module_id: int
    object_type: str
    object_id: int
    code: str
    id: uuid.UUID

    modified_date: datetime
    title: str

    object_statics: ObjectStaticShort | None = None
    module_object_context: ModuleObjectContextShort | None = None

    model_config = ConfigDict(from_attributes=True)


class Module(BaseModel):
    module_id: int
    created_date: datetime
    modified_date: datetime
    created_by_id: uuid.UUID
    modified_by_id: uuid.UUID
    activated: bool
    closed: bool
    successful: bool
    temporary_locked: bool
    title: str
    description: str
    module_manager_1_id: uuid.UUID
    module_manager_2_id: uuid.UUID | None = None
    status: ModuleStatus | None = None

    created_by: UserShort | None = None
    modified_by: UserShort | None = None
    module_manager_1: UserShort | None = None
    module_manager_2: UserShort | None = None

    model_config = ConfigDict(from_attributes=True)


class PublicModuleShort(BaseModel):
    module_id: int
    title: str
    description: str
    status: ModuleStatus | None = None

    @field_validator("title", "description", mode="before")
    def default_empty_string(cls, v):
        return v or ""

    model_config = ConfigDict(from_attributes=True)


class ModuleSortColumn(str, Enum):
    module_id = "module_id"
    title = "title"
    created_date = "created_date"
    modified_date = "modified_date"
    activated = "activated"
    closed = "closed"
    successful = "successful"
    temporary_locked = "temporary_locked"


class GenericObjectShort(BaseModel):
    object_type: str
    object_id: int
    id: uuid.UUID
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)
