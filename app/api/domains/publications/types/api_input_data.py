from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from app.api.domains.publications.types.enums import MutationStrategy, PackageType, PurposeType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementMetadata, AnnouncementProcedural
from app.core.tables.publications import PublicationAnnouncementTable, PublicationVersionTable


@dataclass
class BillFrbr:
    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/bill/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression


@dataclass
class ActFrbr:
    Act_ID: int

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/act/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression

    def __repr__(self) -> str:
        return f"""
        ActFrbr(
            Work={self.get_work()},
            Expression_Version={self.get_expression_version()},
        )
        """


@dataclass
class DocFrbr:
    Document_Type: str

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Expression_Language: str
    Expression_Date: str
    Expression_Version: int

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/doc/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        return expression


@dataclass
class Purpose:
    Purpose_Type: PurposeType
    Effective_Date: Optional[date]
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str


@dataclass
class OwData:
    ow_objects: Dict[str, Any] = field(default_factory=dict)
    terminated_ow_ids: List[str] = field(default_factory=list)


@dataclass
class PublicationData:
    objects: List[dict]
    documents: List[dict]
    assets: List[dict]
    werkingsgebieden: List[dict]
    bill_attachments: List[Dict]
    area_of_jurisdiction: dict
    parsed_template: str


@dataclass
class ActMutation:
    Consolidated_Act_Frbr: ActFrbr
    Consolidated_Act_Text: str
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]
    Removed_Werkingsgebieden: List[dict]


@dataclass
class ApiActInputData:
    Bill_Frbr: BillFrbr
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
    Publication_Data: PublicationData
    Package_Type: PackageType
    Publication_Version: PublicationVersionTable
    Act_Mutation: Optional[ActMutation]
    Ow_Data: OwData
    Mutation_Strategy: MutationStrategy


@dataclass
class ApiAnnouncementInputData:
    Doc_Frbr: DocFrbr
    About_Bill_Frbr: BillFrbr
    About_Act_Frbr: ActFrbr
    Package_Type: PackageType
    Announcement: PublicationAnnouncementTable
    Announcement_Metadata: AnnouncementMetadata
    Announcement_Procedural: AnnouncementProcedural
    Announcement_Content: AnnouncementContent
