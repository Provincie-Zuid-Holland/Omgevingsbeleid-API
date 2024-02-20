import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.extensions.publications.enums import DocumentType, PackageEventType, ProcedureStepType, ProcedureType


class PublicationConfig(BaseModel):
    ID: int
    Created_Date: datetime
    Province_ID: str
    Authority_ID: str
    Submitter_ID: str
    Jurisdiction: str
    Subjects: str
    Governing_Body_Type: str
    Act_Componentname: str
    Administrative_Borders_ID: str
    Administrative_Borders_Domain: str
    Administrative_Borders_Date: date

    DSO_STOP_VERSION: str
    DSO_TPOD_VERSION: str
    DSO_BHKV_VERSION: str

    class Config:
        orm_mode = True


class Publication(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Module_ID: int
    Template_ID: Optional[int]
    Document_Type: DocumentType
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
    Number: Optional[str]
    Content: str


class AmendmentArticle(Article):
    """
    STOP WijzigingArtikel
    """


class BillArticle(Article):
    """
    tekst_artikel
    """


class TimeArticle(Article):
    """
    tijd_artikel
    """


class ProcedureStep(BaseModel):
    """
    STOP Procedurestap
    """

    Step_Type: ProcedureStepType
    Conclusion_Date: date


class ProcedureData(BaseModel):
    """
    STOP Procedureverloop
    """

    Announcement_Date: date  # BekendOp
    Steps: List[ProcedureStep]  # Procedurestappen


class BillData(BaseModel):
    Bill_Title: str  # Officiele titel
    Regulation_Title: str  # Regeling opschrift
    Preamble: Optional[str]  # Aanhef
    Amendment_Article: Optional[AmendmentArticle]  # WijzigingArtikel
    Articles: Optional[List[BillArticle]]  # tekst Artikel
    Time_Article: Optional[TimeArticle]  # tijdArtikel
    Closing: str  # Sluiting
    Signature: str  # Ondertekening


class PublicationBill(BaseModel):
    """
    STOP Besluit
    """

    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Publication_UUID: uuid.UUID
    Module_Status_ID: int

    Version_ID: Optional[int]
    Procedure_Type: ProcedureType
    Is_Official: bool
    Effective_Date: date
    Announcement_Date: date
    PZH_Bill_Identifier: Optional[str]

    Bill_Data: Optional[BillData]
    Procedure_Data: Optional[ProcedureData]

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
    bill_expression_date: date  # expression_datum
    bill_expression_version: str  # expression_versie
    bill_expression_misc: Optional[str]  # expression_overig

    # Fields for act_frbr
    act_work_country: str  # work_land
    act_work_date: str  # work_datum
    act_work_misc: Optional[str]  # work_overig
    act_expression_lang: str  # expression_taal
    act_expression_date: date  # expression_datum
    act_expression_version: str  # expression_versie
    act_expression_misc: Optional[str]  # expression_overig

    def get_target_info(self) -> Dict[str, Optional[str]]:
        """
        target == DSO doel
        """
        # Just use work version since we will not need seperate target joins for now
        # could be changed to custom name db field if nessessary
        target = f"Instelling-{self.bill_work_misc}-{self.bill_expression_version}"
        return {"year": self.bill_expression_date.year, "target_name": target}

    def get_besluit_frbr(self) -> Dict[str, Optional[str]]:
        # to export for dso input_data
        return {
            "work_land": self.bill_work_country,
            "work_datum": self.bill_work_date,
            "work_overig": self.bill_work_misc,
            "expression_taal": self.bill_expression_lang,
            "expression_datum": self.bill_expression_date if self.bill_expression_date else None,
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
            "expression_datum": self.act_expression_date if self.act_expression_date else None,
            "expression_versie": self.act_expression_version,
            "expression_overig": self.act_expression_misc,
        }

    def as_filename(self) -> str:
        pattern = f"akn_{self.bill_expression_lang}_bill_pv28-{self.bill_work_misc}.xml"
        return pattern.lower()

    class Config:
        orm_mode = True


class PublicationPackageReport(BaseModel):
    ID: int
    Created_Date: datetime
    Created_By_UUID: uuid.UUID
    Package_UUID: uuid.UUID
    Result: Optional[str]
    Report_Timestamp: Optional[datetime]
    Messages: Optional[str]
    Report_Type: Optional[str]

    class Config:
        orm_mode = True


class PublicationPackage(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Latest_Download_Date: Optional[datetime]
    Latest_Download_By_UUID: Optional[uuid.UUID]

    Bill_UUID: uuid.UUID
    Config_ID: int
    FRBR_ID: int

    Package_Event_Type: PackageEventType
    Publication_Filename: Optional[str]
    Announcement_Date: date  # passed from bill or overwritten on package create

    ZIP_File_Name: Optional[str]
    ZIP_File_Checksum: Optional[str]
    Validation_Status: Optional[str]

    FRBR_Info: Optional[PublicationFRBR]
    Reports: Optional[List[PublicationPackageReport]]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
