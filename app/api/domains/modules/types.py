import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict


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


class FilterObjectCode(BaseModel):
    object_type: str
    lineage_id: int

    def get_code(self) -> str:
        return f"{self.object_type}-{self.lineage_id}"


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
    Module_Object_Status: PublicModuleStatusCode
    Action: ModuleObjectActionFull

    model_config = ConfigDict(from_attributes=True)
