from dataclasses import dataclass
from typing import List, Optional

from app.extensions.publications.enums import PackageType
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
    Expression_Other: Optional[str]

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/bill/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        if self.Expression_Other is not None:
            expression = f"{expression};{self.Expression_Other}"
        return expression


@dataclass
class ActFrbr:
    Document_Type: str
    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str
    Expression_Language: str
    Expression_Date: str
    Expression_Version: int
    Expression_Other: Optional[str]

    def get_work(self) -> str:
        work: str = f"/akn/{self.Work_Country}/act/{self.Work_Province_ID}/{self.Work_Date}/{self.Work_Other}"
        return work

    def get_expression_version(self) -> str:
        expression: str = f"{self.Expression_Language}@{self.Expression_Date};{self.Expression_Version}"
        if self.Expression_Other is not None:
            expression = f"{expression};{self.Expression_Other}"
        return expression


@dataclass
class PublicationData:
    objects: List[dict]
    assets: List[dict]
    werkingsgebieden: List[dict]
    area_of_juristiction: dict
    parsed_template: str


@dataclass
class ApiInputData:
    Bill_Frbr: BillFrbr
    Act_Frbr: ActFrbr
    Publication_Data: PublicationData
    Package_Type: PackageType
    Publication_Version: PublicationVersionTable
