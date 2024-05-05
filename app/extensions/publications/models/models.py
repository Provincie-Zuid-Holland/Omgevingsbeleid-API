import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.extensions.modules.models.models import ModuleStatus
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
    Field_Map: List[str]

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
    Administrative_Borders_Date: date
    Created_Date: datetime

    class Config:
        orm_mode = True


class PublicationAct(BaseModel):
    UUID: uuid.UUID
    Title: str
    Is_Active: bool
    Environment: PublicationEnvironment
    Document_Type: str
    Procedure_Type: str
    Metadata: dict

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationActShort(BaseModel):
    UUID: uuid.UUID
    Title: str
    Is_Active: bool
    Environment_UUID: uuid.UUID
    Document_Type: str
    Procedure_Type: str

    Work_Province_ID: str
    Work_Country: str
    Work_Date: str
    Work_Other: str

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class Publication(BaseModel):
    UUID: uuid.UUID

    Module_ID: int
    Title: str
    Is_Locked: bool
    Document_Type: str
    Procedure_Type: str
    Template_UUID: Optional[uuid.UUID]
    Environment_UUID: Optional[uuid.UUID]
    Act_UUID: Optional[uuid.UUID]

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationShort(BaseModel):
    UUID: uuid.UUID

    Module_ID: int
    Title: str
    Is_Locked: bool
    Document_Type: str
    Procedure_Type: str
    Template_UUID: Optional[uuid.UUID]
    Environment_UUID: Optional[uuid.UUID]
    Act_UUID: Optional[uuid.UUID]

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class Article(BaseModel):
    Label: str = Field("")  # @deprecated
    Number: str
    Content: str


class BillMetadata(BaseModel):
    Official_Title: str = Field("")
    Quote_Title: str = Field("")
    Subjects: List[str] = Field([])
    Jurisdictions: List[str] = Field([])

    class Config:
        orm_mode = True


class Appendix(BaseModel):
    Number: str
    Title: str
    Content: str

    class Config:
        orm_mode = True


class Motivation(BaseModel):
    Title: str
    Content: str
    Appendices: List[Appendix] = Field([])

    class Config:
        orm_mode = True


MotivationClass = Motivation


class BillCompact(BaseModel):
    Component_Name: str = Field("")
    Preamble: str = Field("")
    Closing: str = Field("")
    Signed: str = Field("")
    Amendment_Article: str = Field("")
    Time_Article: str = Field("")
    Custom_Articles: List[Article] = Field([])

    Appendices: List[Appendix] = Field([])
    Motivation: Optional[MotivationClass] = Field(None)

    class Config:
        orm_mode = True


class Procedural(BaseModel):
    Enactment_Date: Optional[str] = Field(None)
    Signed_Date: Optional[str] = Field(None)
    Procedural_Announcement_Date: Optional[str] = Field(None)

    @validator("Enactment_Date", "Signed_Date", "Procedural_Announcement_Date")
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    class Config:
        orm_mode = True


class ProceduralValidated(BaseModel):
    Enactment_Date: Optional[str] = Field(None)
    Signed_Date: str
    Procedural_Announcement_Date: str

    @validator("Enactment_Date", "Signed_Date", "Procedural_Announcement_Date")
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
    Official_Title: str = Field("")
    Quote_Title: str = Field("")
    Subjects: List[str] = Field([])
    Jurisdictions: List[str] = Field([])

    class Config:
        orm_mode = True


class PublicationVersionValidated(BaseModel):
    UUID: uuid.UUID

    Procedure_Type: str

    Bill_Metadata: BillMetadata
    Bill_Compact: BillCompact
    Procedural: ProceduralValidated

    Effective_Date: date
    Announcement_Date: date

    class Config:
        orm_mode = True


class AttachmentShort(BaseModel):
    File_UUID: uuid.UUID
    Filename: str
    Title: str
    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationVersion(BaseModel):
    UUID: uuid.UUID

    Publication: PublicationShort
    Module_Status: ModuleStatus

    Bill_Metadata: dict
    Bill_Compact: dict
    Procedural: dict

    Effective_Date: Optional[date]
    Announcement_Date: Optional[date]
    Is_Locked: bool
    Is_Valid: bool = Field(False)

    Created_Date: datetime
    Modified_Date: datetime

    Attachments: List[AttachmentShort]

    class Config:
        orm_mode = True


class PublicationVersionShort(BaseModel):
    UUID: uuid.UUID

    Publication_UUID: uuid.UUID
    Module_Status: ModuleStatus

    Bill_Metadata: dict

    Effective_Date: Optional[date]
    Announcement_Date: Optional[date]
    Is_Locked: bool

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationActPackageReportShort(BaseModel):
    UUID: uuid.UUID
    Act_Package_UUID: uuid.UUID

    Report_Status: str
    Filename: str
    Main_Outcome: str

    Created_Date: datetime

    class Config:
        orm_mode = True


class PublicationActPackageReport(BaseModel):
    UUID: uuid.UUID
    Act_Package_UUID: uuid.UUID

    Report_Status: str
    Filename: str
    Source_Document: str
    Main_Outcome: str
    Sub_Delivery_ID: str
    Sub_Progress: str
    Sub_Outcome: str

    Created_Date: datetime

    class Config:
        orm_mode = True


class PackageZipShort(BaseModel):
    UUID: uuid.UUID
    Filename: str
    Latest_Download_Date: Optional[datetime]
    Latest_Download_By_UUID: Optional[uuid.UUID]

    class Config:
        orm_mode = True


class PublicationPackage(BaseModel):
    UUID: uuid.UUID

    Package_Type: str
    Report_Status: str
    Delivery_ID: str

    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    Zip: PackageZipShort

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class PublicationPackageShort(BaseModel):
    UUID: uuid.UUID

    Package_Type: str
    Report_Status: str
    Delivery_ID: str

    Created_Date: datetime
    Modified_Date: datetime
    Created_By_UUID: uuid.UUID
    Modified_By_UUID: uuid.UUID

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class AnnouncementMetadata(BaseModel):
    Official_Title: str = Field("")
    Subjects: List[str] = Field([])

    class Config:
        orm_mode = True


class AnnouncementProcedural(BaseModel):
    Procedural_Announcement_Date: Optional[str] = Field(None)
    Begin_Inspection_Period_Date: Optional[str] = Field(None)
    End_Inspection_Period_Date: Optional[str] = Field(None)

    @validator(
        "Procedural_Announcement_Date",
        "Begin_Inspection_Period_Date",
        "End_Inspection_Period_Date",
    )
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    class Config:
        orm_mode = True


class AnnouncementText(BaseModel):
    Title: str
    Description: str


class AnnouncementContent(BaseModel):
    Texts: List[AnnouncementText]


class PublicationAnnouncement(BaseModel):
    UUID: uuid.UUID

    Act_Package: PublicationPackageShort
    Publication: PublicationShort

    Metadata: dict
    Procedural: dict
    Content: dict

    Announcement_Date: Optional[date]
    Is_Locked: bool

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationAnnouncementShort(BaseModel):
    UUID: uuid.UUID

    Metadata: dict

    Announcement_Date: Optional[date]
    Is_Locked: bool

    Created_Date: datetime
    Modified_Date: datetime

    class Config:
        orm_mode = True


class PublicationAnnouncementPackageReportShort(BaseModel):
    UUID: uuid.UUID
    Announcement_Package_UUID: uuid.UUID

    Report_Status: str
    Filename: str
    Main_Outcome: str

    Created_Date: datetime

    class Config:
        orm_mode = True


class PublicationAnnouncementPackageReport(BaseModel):
    UUID: uuid.UUID
    Announcement_Package_UUID: uuid.UUID

    Report_Status: str
    Filename: str
    Source_Document: str
    Main_Outcome: str
    Sub_Delivery_ID: str
    Sub_Progress: str
    Sub_Outcome: str

    Created_Date: datetime

    class Config:
        orm_mode = True
