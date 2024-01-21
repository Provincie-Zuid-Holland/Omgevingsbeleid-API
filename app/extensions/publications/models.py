import uuid
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.extensions.publications.enums import Document_Type, Bill_Type, Package_Event_Type


class PublicationConfig(BaseModel):
    ID: int
    Created_Date: datetime
    Modified_Date: datetime

    Province_ID: str
    Authority_ID: str
    Submitter_ID: str

    Jurisdiction: str
    Subjects: str

    dso_stop_version: str
    dso_tpod_version: str
    dso_bhkv_version: str

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

    pass


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
    Amendment_Article: Optional[AmendmentArticle] # WijzigingArtikel
    Articles: Optional[List[BillArticle]]  # Artikel
    Closing: str  # Sluiting
    Signature: str  # Ondertekening


class PublicationBill(BaseModel):
    """
    STOP Besluit
    """
    UUID: uuid.UUID
    Version_ID: Optional[int]
    Module_ID: int
    Module_Status_ID: int

    Created_Date: datetime = datetime.now()
    Modified_Date: datetime = datetime.now()

    Document_Type: Document_Type
    Bill_Type: Bill_Type
    Effective_Date: Optional[datetime]
    Announcement_Date: Optional[datetime]
    Bill_Data: Optional[Bill_Data]
    Procedure_Data: Optional[Procedure_Data]

    @classmethod
    def from_orm(cls, obj):
        # auto convert and validate db json to the Bill_Data schema
        if isinstance(obj.Bill_Data, dict):
            obj.Bill_Data = Bill_Data(**obj.Bill_Data)
        if isinstance(obj.Procedure_Data, dict):
            obj.Procedure_Data = Procedure_Data(**obj.Procedure_Data)
        return super().from_orm(obj)

    class Config:
        orm_mode = True


class PublicationPackage(BaseModel):
    UUID: uuid.UUID
    Created_Date: datetime
    Modified_Date: datetime

    Bill_UUID: uuid.UUID

    Package_Event_Type: Package_Event_Type
    Publication_Filename: Optional[str]
    Announcement_Date: datetime

    Publication_Bill: Optional[PublicationBill]

    Province_ID: str
    Submitter_ID: str
    Authority_ID: str
    Jurisdiction: str
    Subjects: str
    dso_stop_version: str
    dso_tpod_version: str
    dso_bhkv_version: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
