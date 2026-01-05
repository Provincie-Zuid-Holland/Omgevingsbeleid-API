import uuid
from abc import ABCMeta
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.publications.types.enums import PurposeType

from .models import Asset, Document, Frbr, Purpose, Gebiedengroep, Gebiedsaanwijzing, WidData, OwState


class Action(BaseModel, metaclass=ABCMeta):
    pass


class AddAnnouncementAction(Action):
    Doc_Frbr: Frbr
    About_Act_Frbr: Frbr
    About_Bill_Frbr: Frbr
    Document_Type: str
    Procedure_Type: str


class AddPublicationAction(Action):
    Act_Frbr: Frbr
    Bill_Frbr: Frbr
    Consolidation_Purpose: Purpose
    Document_Type: str
    Procedure_Type: str
    # @todo
    # Gebieden: Dict[str, Gebied]
    Gebiedengroepen: Dict[str, Gebiedengroep]
    Gebiedsaanwijzingen: List[Gebiedsaanwijzing]
    Documents: Dict[int, Document]
    Assets: Dict[str, Asset]
    Wid_Data: WidData
    Ow_State: OwState
    Act_Text: str
    Publication_Version_UUID: str


class AddPurposeAction(Action):
    Purpose_Type: PurposeType
    Effective_Date: Optional[date] = None
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str

    def get_effective_date_str(self) -> str:
        if self.Effective_Date is None:
            return ""

        return self.Effective_Date.strftime("%Y-%m-%d")


# @todo: Check if these are needed
# @todo: I think this should be part of the AddPublicationAction
class AddAreaOfJurisdictionAction(Action):
    UUID: uuid.UUID
    Administrative_Borders_ID: str
    Act_Frbr: ActFrbr


class ConsolidateWerkingsgebiedAction(Action):
    UUID: uuid.UUID
    Object_ID: int
    Work: str
    Expression_Version: str
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
