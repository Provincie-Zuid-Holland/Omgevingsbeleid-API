import uuid
from abc import ABCMeta
from datetime import date

from pydantic import BaseModel

from app.api.domains.publications.types.api_input_data import ActFrbr
from app.api.domains.publications.types.enums import PurposeType

from .models import Asset, Document, Frbr, Gebiedengroep, Gebiedsaanwijzing, Gio, OwState, Purpose, WidData


class Action(BaseModel, metaclass=ABCMeta):
    pass


class AddAnnouncementAction(Action):
    doc_frbr: Frbr
    about_act_frbr: Frbr
    about_bill_frbr: Frbr
    document_type: str
    procedure_type: str


class AddPublicationAction(Action):
    act_frbr: Frbr
    bill_frbr: Frbr
    consolidation_purpose: Purpose
    document_type: str
    procedure_type: str
    gios: dict[str, Gio]
    gebiedengroepen: dict[str, Gebiedengroep]
    gebiedsaanwijzingen: dict[str, Gebiedsaanwijzing]
    documents: dict[int, Document]
    assets: dict[str, Asset]
    wid_data: WidData
    ow_state: OwState
    act_text: str
    publication_version_uuid: str


class AddPurposeAction(Action):
    purpose_type: PurposeType
    effective_date: date | None = None
    work_province_id: str
    work_date: str
    work_other: str

    def get_effective_date_str(self) -> str:
        if self.effective_date is None:
            return ""

        return self.effective_date.strftime("%Y-%m-%d")


# @todo: Check if these are needed
# @todo: I think this should be part of the AddPublicationAction
class AddAreaOfJurisdictionAction(Action):
    uuid: uuid.UUID
    administrative_borders_id: str
    act_frbr: ActFrbr


class ConsolidateWerkingsgebiedAction(Action):
    uuid: uuid.UUID
    object_id: int
    work: str
    expression_version: str
    act_frbr: ActFrbr
    consolidation_purpose: Purpose
