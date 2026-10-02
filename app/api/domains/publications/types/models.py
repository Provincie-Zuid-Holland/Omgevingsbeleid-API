import uuid
from datetime import date, datetime
from typing import Any

from dso.services.koop.waardelijsten.gen import BestuursorgaanType, OnderwerpType, RechtsgebiedType
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import ErrorDetails

from app.api.domains.modules.types import ModuleStatus
from app.api.domains.publications.types.enums import MutationStrategy, PublicationVersionStatus


# This model is meant for frontend
class Waardelijsten(BaseModel):
    Rechtsgebied: RechtsgebiedType
    Onderwerp: OnderwerpType
    Bestuursorgaan: BestuursorgaanType


class PublicationTemplate(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    is_active: bool
    document_type: str
    object_types: Any = None
    text_template: str
    object_templates: Any = None
    object_field_map: Any = None

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationEnvironment(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    province_id: str
    authority_id: str
    submitter_id: str
    governing_body_type: str
    frbr_country: str
    frbr_language: str
    is_active: bool
    has_state: bool
    can_validate: bool
    can_publicate: bool
    is_locked: bool

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAOJ(BaseModel):
    id: uuid.UUID
    administrative_borders_id: str
    administrative_borders_domain: str
    administrative_borders_date: date
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAct(BaseModel):
    id: uuid.UUID
    title: str
    is_active: bool
    environment: PublicationEnvironment
    document_type: str
    meta_data: dict

    work_province_id: str
    work_country: str
    work_date: str
    work_other: str

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationActShort(BaseModel):
    id: uuid.UUID
    title: str
    is_active: bool
    environment_id: uuid.UUID
    document_type: str

    work_province_id: str
    work_country: str
    work_date: str
    work_other: str

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class Publication(BaseModel):
    id: uuid.UUID

    module_id: int
    is_locked: bool
    document_type: str
    procedure_type: str
    template_id: uuid.UUID | None = None
    environment_id: uuid.UUID | None = None
    act_id: uuid.UUID | None = None

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationShort(BaseModel):
    id: uuid.UUID
    module_id: int
    is_locked: bool
    document_type: str
    procedure_type: str
    template_id: uuid.UUID | None = None
    environment_id: uuid.UUID | None = None
    act_id: uuid.UUID | None = None

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class Article(BaseModel):
    label: str = Field("")  # @deprecated
    number: str
    content: str


class BillMetadata(BaseModel):
    official_title: str = Field("")
    quote_title: str = Field("")
    subjects: list[str] = Field([])
    jurisdictions: list[str] = Field([])

    model_config = ConfigDict(from_attributes=True)


class Appendix(BaseModel):
    number: str
    title: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class Paragraph(BaseModel):
    content: str


ParagraphClass = Paragraph


class Motivation(BaseModel):
    number: str | None = Field(None)
    title: str
    content: str
    appendices: list[Appendix] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AmendmentAppendix(BaseModel):
    number: str
    title: str

    model_config = ConfigDict(from_attributes=True)


MotivationClass = Motivation


class BillCompact(BaseModel):
    preamble: str = Field("")
    closing: str = Field("")
    signed: str = Field("")
    amendment_article: str = Field("")
    amendment_appendix: AmendmentAppendix = Field(
        AmendmentAppendix(
            number="A",
            title="bij Artikel I",
        )
    )
    time_article: str = Field("")
    custom_articles: list[Article] = Field([])

    appendices: list[Appendix] = Field([])
    motivation: MotivationClass | None = Field(None)

    model_config = ConfigDict(from_attributes=True)


class Procedural(BaseModel):
    enactment_date: str | None = Field(None)
    signed_date: str | None = Field(None)
    procedural_announcement_date: str | None = Field(None)

    @field_validator("enactment_date", "signed_date", "procedural_announcement_date")
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    model_config = ConfigDict(from_attributes=True)


ProceduralClass = Procedural


class ProceduralValidated(BaseModel):
    enactment_date: str | None = Field(None)
    signed_date: str
    procedural_announcement_date: str

    @field_validator("enactment_date", "signed_date", "procedural_announcement_date")
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    model_config = ConfigDict(from_attributes=True)


class ActMetadata(BaseModel):
    official_title: str = Field("")
    quote_title: str = Field("")
    subjects: list[str] = Field([])
    jurisdictions: list[str] = Field([])

    model_config = ConfigDict(from_attributes=True)


class PublicationVersionFinalValidated(BaseModel):
    id: uuid.UUID

    bill_metadata: BillMetadata
    bill_compact: BillCompact
    procedural: ProceduralValidated

    effective_date: date
    announcement_date: date

    model_config = ConfigDict(from_attributes=True)


class PublicationVersionDraftValidated(BaseModel):
    id: uuid.UUID

    bill_metadata: BillMetadata
    bill_compact: BillCompact
    procedural: ProceduralValidated

    announcement_date: date

    model_config = ConfigDict(from_attributes=True)


class AttachmentShort(BaseModel):
    id: int
    file_id: uuid.UUID
    filename: str
    title: str
    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationVersion(BaseModel):
    id: uuid.UUID

    publication: PublicationShort
    module_status: ModuleStatus

    bill_metadata: dict
    bill_compact: dict
    procedural: dict
    effective_date: date | None = None
    announcement_date: date | None = None
    is_locked: bool
    status: PublicationVersionStatus
    mutation_strategy: MutationStrategy

    created_date: datetime
    modified_date: datetime

    attachments: list[AttachmentShort]

    errors: list[ErrorDetails] = Field([])

    model_config = ConfigDict(from_attributes=True)


class PublicationPackageShort(BaseModel):
    id: uuid.UUID

    package_type: str
    report_status: str
    delivery_id: str

    created_date: datetime
    modified_date: datetime
    created_by_id: uuid.UUID
    modified_by_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class PublicationVersionShort(BaseModel):
    id: uuid.UUID

    publication_id: uuid.UUID
    module_status: ModuleStatus

    bill_metadata: dict

    effective_date: date | None = None
    announcement_date: date | None = None
    is_locked: bool
    status: PublicationVersionStatus
    procedural: ProceduralClass | None = None

    created_date: datetime
    modified_date: datetime

    act_packages: list[PublicationPackageShort]

    model_config = ConfigDict(from_attributes=True)


class PublicationActPackageReportShort(BaseModel):
    id: uuid.UUID
    act_package_id: uuid.UUID

    report_status: str
    filename: str
    main_outcome: str

    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationActPackageReport(BaseModel):
    id: uuid.UUID
    act_package_id: uuid.UUID

    report_status: str
    filename: str
    source_document: str
    main_outcome: str
    sub_delivery_id: str
    sub_progress: str
    sub_outcome: str

    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PackageZipShort(BaseModel):
    id: uuid.UUID
    filename: str
    latest_download_date: datetime | None = None
    latest_download_by_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class PublicationPackage(BaseModel):
    id: uuid.UUID

    package_type: str
    report_status: str
    delivery_id: str

    created_date: datetime
    modified_date: datetime
    created_by_id: uuid.UUID
    modified_by_id: uuid.UUID

    zip: PackageZipShort

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class PublicationActPackage(PublicationPackage):
    module_id: int | None = None
    module_status: ModuleStatus | None = None


class AnnouncementMetadata(BaseModel):
    official_title: str = Field("")
    subjects: list[str] = Field([])

    model_config = ConfigDict(from_attributes=True)


class AnnouncementProcedural(BaseModel):
    procedural_announcement_date: str | None = Field(None)
    begin_inspection_period_date: str | None = Field(None)
    end_inspection_period_date: str | None = Field(None)

    @field_validator("procedural_announcement_date", "begin_inspection_period_date", "end_inspection_period_date")
    def validate_date(cls, value):
        if value is not None:
            try:
                datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got {value}")
        return value

    model_config = ConfigDict(from_attributes=True)


class AnnouncementText(BaseModel):
    title: str | None
    description: str


class AnnouncementContent(BaseModel):
    texts: list[AnnouncementText]


class PublicationAnnouncement(BaseModel):
    id: uuid.UUID

    act_package: PublicationPackageShort
    publication: PublicationShort

    meta_data: dict
    procedural: dict
    content: dict

    announcement_date: date | None = None
    is_locked: bool

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAnnouncementShort(BaseModel):
    id: uuid.UUID

    meta_data: dict

    announcement_date: date | None = None
    is_locked: bool

    created_date: datetime
    modified_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAnnouncementPackageReportShort(BaseModel):
    id: uuid.UUID
    announcement_package_id: uuid.UUID

    report_status: str
    filename: str
    main_outcome: str

    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicationAnnouncementPackageReport(BaseModel):
    id: uuid.UUID
    announcement_package_id: uuid.UUID

    report_status: str
    filename: str
    source_document: str
    main_outcome: str
    sub_delivery_id: str
    sub_progress: str
    sub_outcome: str

    created_date: datetime

    model_config = ConfigDict(from_attributes=True)
