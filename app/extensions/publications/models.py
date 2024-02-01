import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.extensions.publications.enums import Document_Type, Package_Event_Type, Procedure_Type


class PublicationConfig(BaseModel):
    ID: int
    Created_Date: datetime
    Province_ID: str
    Authority_ID: str
    Submitter_ID: str
    Jurisdiction: str
    Subjects: str
    DSO_STOP_VERSION: str
    DSO_TPOD_VERSION: str
    DSO_BHKV_VERSION: str

    class Config:
        orm_mode = True


class Publication(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Module_ID: int
    Template_ID: Optional[int]
    Document_Type: Document_Type
    Work_ID: int
    Official_Title: str
    Regulation_Title: str

    class Config:
        orm_mode = True


class Article(BaseModel):
    """
    STOP Artikel
    """

    Label: str
    Number: str
    Content: str


class AmendmentArticle(Article):
    """
    STOP WijzigingArtikel
    """


class BillArticle(Article):
    pass


class ProcedureStep(BaseModel):
    """
    STOP Procedurestap
    """

    Step_Type: str
    Conclusion_Date: datetime


class Procedure_Data(BaseModel):
    """
    STOP Procedureverloop
    """

    Announcement_Date: datetime  # BekendOp
    Steps: List[ProcedureStep] = []  # Procedurestappen


class Bill_Data(BaseModel):
    Bill_Title: str  # Officiele titel
    Regulation_Title: str  # Regeling opschrift
    Preamble: Optional[str]  # Aanhef
    Amendment_Article: Optional[AmendmentArticle]  # WijzigingArtikel
    Articles: Optional[List[BillArticle]]  # Artikel
    Closing: str  # Sluiting
    Signature: str  # Ondertekening


class PublicationBill(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Module_ID: int
    Template_ID: Optional[int]
    Work_ID: Optional[int]

    Document_Type: Document_Type
    Official_Title: str
    Regulation_Title: str

    class Config:
        orm_mode = True


class PublicationBill(BaseModel):
    """
    STOP Besluit
    """

    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Publication_UUID: uuid.UUID
    Module_Status_ID: int

    Version_ID: Optional[int]
    Procedure_Type: Procedure_Type
    Is_Official: bool
    Effective_Date: datetime
    Announcement_Date: datetime

    Bill_Data: Optional[Bill_Data]
    Procedure_Data: Optional[Procedure_Data]

    class Config:
        orm_mode = True


class PublicationFRBR(BaseModel):
    ID: int
    Created_Date: datetime

    # Fields for bill_frbr
    bill_work_country: str  # work_land
    bill_work_date: str  # work_datum
    bill_work_misc: Optional[str]  # work_overig
    bill_expression_lang: str  # expression_taal
    bill_expression_date: datetime  # expression_datum
    bill_expression_version: str  # expression_versie
    bill_expression_misc: Optional[str]  # expression_overig

    # Fields for act_frbr
    act_work_country: str  # work_land
    act_work_date: str  # work_datum
    act_work_misc: Optional[str]  # work_overig
    act_expression_lang: str  # expression_taal
    act_expression_date: datetime  # expression_datum
    act_expression_version: str  # expression_versie
    act_expression_misc: Optional[str]  # expression_overig

    def get_besluit_frbr(self) -> Dict[str, Optional[str]]:
        # to export for dso input_data
        return {
            "work_land": self.bill_work_country,
            "work_datum": self.bill_work_date,
            "work_overig": self.bill_work_misc,
            "expression_taal": self.bill_expression_lang,
            "expression_datum": self.bill_expression_date.strftime("%Y-%m-%d") if self.bill_expression_date else None,
            "expression_versie": self.bill_expression_version,
            "expression_overig": self.bill_expression_misc,
        }

    def get_regeling_frbr(self) -> Dict[str, Optional[str]]:
        # to export for dso input_data
        return {
            "work_land": self.act_work_country,
            "work_datum": self.act_work_date,
            "work_overig": self.act_work_misc,
            "expression_taal": self.act_expression_lang,
            "expression_datum": self.act_expression_date.strftime("%Y-%m-%d") if self.act_expression_date else None,
            "expression_versie": self.act_expression_version,
            "expression_overig": self.act_expression_misc,
        }

    def as_filename(self) -> str:
        pattern = f"akn_{self.bill_expression_lang}_bill_pv28-{self.bill_work_misc}.xml"
        return pattern.lower()

    class Config:
        orm_mode = True


class PublicationPackage(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Bill_UUID: uuid.UUID
    Config_ID: int
    FRBR_ID: int

    Package_Event_Type: Package_Event_Type
    Publication_Filename: Optional[str]
    Announcement_Date: datetime
    Validated_At: Optional[datetime]

    Publication_Config: Optional[PublicationConfig]
    Publication_Bill: Optional[PublicationBill]
    FRBR_Info: Optional[PublicationFRBR]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
