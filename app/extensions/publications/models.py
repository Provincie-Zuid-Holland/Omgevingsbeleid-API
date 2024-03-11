import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.extensions.modules.models.models import ModuleStatus
from app.extensions.publications.enums import DocumentType
from app.extensions.publications.waardelijsten import Bestuursorgaan, Onderwerp, Rechtsgebied


# This model is meant for frontend
class Waardelijsten(BaseModel):
    Rechtsgebied: Rechtsgebied
    Onderwerp: Onderwerp
    Bestuursorgaan: Bestuursorgaan


class PublicationTemplate(BaseModel):
    UUID: uuid.UUID
    Title: str
    Description: str
    Is_Active: bool
    Document_Type: str
    Object_Types: List[str]
    Text_Template: str
    Object_Templates: Dict[str, str]
    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationEnvironment(BaseModel):
    UUID: uuid.UUID
    Title: str
    Description: str
    Province_ID: str
    Authority_ID: str
    Submitter_ID: str
    Governing_Body_Type: str
    Frbr_Country: str
    Frbr_Language: str
    Is_Active: bool
    Has_State: bool
    Can_Validate: bool
    Can_Publicate: bool
    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationAOJ(BaseModel):
    UUID: uuid.UUID
    Administrative_Borders_ID: str
    Administrative_Borders_Domain: str
    Administrative_Borders_Date: str
    Created_Date: datetime

    class Config:
        orm_mode = True


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

    Module_ID: int
    Document_Type: DocumentType
    Template_UUID: Optional[uuid.UUID]

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationShort(BaseModel):
    UUID: uuid.UUID

    Module_ID: int
    Document_Type: str
    Template_UUID: Optional[uuid.UUID]

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class BillMetadata(BaseModel):
    OfficialTitle: str = Field("")
    Subjects: List[str] = Field([])
    Jurisdictions: List[str] = Field([])

    class Config:
        orm_mode = True


class BillCompact(BaseModel):
    Preamble: str = Field("")
    Closing: str = Field("")
    Signed: str = Field("")
    AmendmentArticle: str = Field("")
    TimeArticle: str = Field("")

    class Config:
        orm_mode = True


class Procedural(BaseModel):
    EnactmentDate: Optional[str] = Field(None)
    SignedDate: Optional[str] = Field(None)

    @validator("EnactmentDate", "SignedDate")
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    class Config:
        orm_mode = True


class ActMetadata(BaseModel):
    OfficialTitle: str = Field("")
    QuoteTitle: str = Field("")
    Subjects: List[str] = Field([])
    Jurisdictions: List[str] = Field([])

    class Config:
        orm_mode = True


class PublicationVersion(BaseModel):
    UUID: uuid.UUID

    Publication: PublicationShort
    Module_Status: ModuleStatus
    Environment: PublicationEnvironment
    Procedure_Type: str

    Bill_Metadata: dict
    Bill_Compact: dict
    Procedural: dict
    Act_Metadata: dict

    Effective_Date: Optional[date]
    Announcement_Date: Optional[date]
    Locked: bool
    Is_Valid: bool = Field(False)

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationVersionShort(BaseModel):
    UUID: uuid.UUID

    Publication_UUID: uuid.UUID
    Module_Status: ModuleStatus
    Environment_UUID: uuid.UUID
    Procedure_Type: str

    Effective_Date: Optional[date]
    Announcement_Date: Optional[date]
    Locked: bool

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class Article(BaseModel):
    Label: str
    Number: Optional[str]
    Content: str


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

    Validation_Status: Optional[str]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
