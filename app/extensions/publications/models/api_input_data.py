from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from app.extensions.publications.enums import PackageType, PurposeType
from app.extensions.publications.tables.tables import PublicationVersionTable


@dataclass
class BillFrbr:
    # This is the "instrument" not the work document type
    # As the class already represents the Work_Document_Type
    Document_Type: str

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
    Document_Type: str
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
class Purpose:
    Purpose_Type: PurposeType
    Effective_Date: Optional[date]
    Work_Province_ID: str
    Work_Date: str
    Work_Other: str


@dataclass
class OwData:
    Object_Ids: List[str] = field(default_factory=list)
    Object_Map: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class PublicationData:
    objects: List[dict]
    assets: List[dict]
    werkingsgebieden: List[dict]
    area_of_jurisdiction: dict
    parsed_template: str


@dataclass
class ActMutation:
    Consolidated_Act_Frbr: ActFrbr
    Consolidated_Act_Text: str
    Known_Wid_Map: Dict[str, str]
    Known_Wids: List[str]


@dataclass
class ApiInputData:
    Bill_Frbr: BillFrbr
    Act_Frbr: ActFrbr
    Consolidation_Purpose: Purpose
    Publication_Data: PublicationData
    Package_Type: PackageType
    Publication_Version: PublicationVersionTable
    Act_Mutation: Optional[ActMutation]
    Ow_Data: OwData
