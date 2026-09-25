from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import Column, Date, DateTime, ForeignKey, LargeBinary, String, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.types import JSON, Integer

from app.core.db.base import Base
from app.core.db.mixins import UserMetaData
from app.core.tables.modules import ModuleStatusHistoryTable, ModuleTable


class PublicationStorageFileTable(Base):
    __tablename__ = "publication_storage_files"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Lookup for faster access
    lookup: Mapped[str] = mapped_column(Unicode(10), index=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    filename: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    content_type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    binary: Mapped[bytes] = deferred(mapped_column(LargeBinary(), nullable=False))

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


ObjectFieldMapTypeAdapter = TypeAdapter(dict[str, list[str]])


class PublicationTemplateTable(Base, UserMetaData):
    __tablename__ = "publication_templates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Unicode, nullable=False)
    description: Mapped[str] = mapped_column(Unicode, nullable=False)

    is_active: Mapped[bool]
    document_type: Mapped[str] = mapped_column(Unicode, nullable=False)
    object_types: Mapped[Any] = mapped_column(JSON, nullable=False)
    text_template: Mapped[str] = mapped_column(Unicode, nullable=False)
    object_templates: Mapped[Any] = mapped_column(JSON, nullable=False)
    field_map: Mapped[Any] = mapped_column(JSON, nullable=True)
    object_field_map: Mapped[Any] = mapped_column(JSON, nullable=True)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]


class PublicationEnvironmentTable(Base, UserMetaData):
    __tablename__ = "publication_environments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Unicode)

    # Used to map secret data to the environment like API Keys
    code: Mapped[str | None] = mapped_column(Unicode(32), nullable=True)
    description: Mapped[str] = mapped_column(Unicode)

    province_id: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    authority_id: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    submitter_id: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    governing_body_type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    frbr_country: Mapped[str] = mapped_column(Unicode(2), nullable=False)
    frbr_language: Mapped[str] = mapped_column(Unicode(3), nullable=False)

    is_active: Mapped[bool]
    has_state: Mapped[bool]
    can_validate: Mapped[bool]
    can_publicate: Mapped[bool]

    is_locked: Mapped[bool]

    active_state_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_environment_states.id"), nullable=True)
    active_state: Mapped[Optional["PublicationEnvironmentStateTable"]] = relationship(
        "PublicationEnvironmentStateTable",
        primaryjoin="PublicationEnvironmentTable.active_state_id == PublicationEnvironmentStateTable.id",
    )

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]


class PublicationEnvironmentStateTable(Base):
    __tablename__ = "publication_environment_states"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))
    adjust_on_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_environment_states.id"), nullable=True)

    state = Column(JSON)

    is_activated: Mapped[bool]
    activated_datetime: Mapped[datetime | None]

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationAreaOfJurisdictionTable(Base):
    # Ambtsgebied
    __tablename__ = "publication_area_of_jurisdictions"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(Unicode, server_default="")
    administrative_borders_id: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    administrative_borders_domain: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    administrative_borders_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationPurposeTable(Base):
    __tablename__ = "publication_purposes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))
    purpose_type: Mapped[str] = mapped_column(Unicode(50), nullable=False)

    # "Ontwerp" does not have a time
    effective_date: Mapped[date | None]

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_niet-tekst.html#doel
    work_province_id: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_other: Mapped[str] = mapped_column(Unicode(128), nullable=False)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    __table_args__ = (UniqueConstraint("environment_id", "work_other", name="uix_pub_pur_env_other"),)


class PublicationActTable(Base, UserMetaData):
    __tablename__ = "publication_acts"

    # This unique auto increment gives us a small sized unique identifier
    # to consolidate GIO's with.
    id: Mapped[int] = mapped_column(primary_key=True)

    # This UUID would not really be needed
    # But we keep it as it is less confusing that everything is linked by UUID
    uuid: Mapped[UUID] = mapped_column(unique=True)

    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))

    document_type: Mapped[str] = mapped_column(Unicode(50), nullable=False)

    # @deprecated
    procedure_type: Mapped[str | None] = mapped_column(Unicode(50), nullable=True)

    title: Mapped[str] = mapped_column(Unicode)
    is_active: Mapped[bool] = mapped_column(default=False)

    # RegelingMetadata
    meta_data = Column(JSON)
    meta_data_is_locked: Mapped[bool] = mapped_column(default=False)

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html#docbg
    work_province_id: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_country: Mapped[str] = mapped_column(Unicode(2), nullable=False)
    work_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_other: Mapped[str] = mapped_column(Unicode(128), nullable=False)

    withdrawal_purpose_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_purposes.id"), nullable=True)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    environment: Mapped[PublicationEnvironmentTable] = relationship("PublicationEnvironmentTable")
    withdrawal_purpose: Mapped[PublicationPurposeTable | None] = relationship(
        "PublicationPurposeTable",
        primaryjoin="PublicationActTable.withdrawal_purpose_id == PublicationPurposeTable.id",
    )

    __table_args__ = (UniqueConstraint("environment_id", "work_other", name="uix_pub_act_env_other"),)


class PublicationActVersionTable(Base):
    __tablename__ = "publication_act_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    act_id: Mapped[int] = mapped_column(ForeignKey("publication_acts.id"))
    consolidation_purpose_id: Mapped[UUID] = mapped_column(ForeignKey("publication_purposes.id"))

    expression_language: Mapped[str] = mapped_column(Unicode(3), nullable=False)
    expression_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    expression_version: Mapped[int] = mapped_column(Integer, nullable=False)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    act: Mapped[PublicationActTable] = relationship()

    consolidation_purpose: Mapped[PublicationPurposeTable] = relationship(
        "PublicationPurposeTable",
        primaryjoin="PublicationActVersionTable.consolidation_purpose_id == PublicationPurposeTable.id",
    )

    __table_args__ = (UniqueConstraint("act_id", "expression_version", name="uix_act_version"),)


class PublicationTable(Base, UserMetaData):
    __tablename__ = "publications"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    module_id: Mapped[int] = mapped_column(Integer, ForeignKey("modules.module_id"), nullable=False)

    document_type: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    procedure_type: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("publication_templates.id"), nullable=False)
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))
    act_id: Mapped[int] = mapped_column(ForeignKey("publication_acts.id"))

    is_locked: Mapped[bool] = mapped_column(default=False)

    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    modified_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    module: Mapped[ModuleTable] = relationship("ModuleTable")
    template: Mapped["PublicationTemplateTable"] = relationship("PublicationTemplateTable")
    environment: Mapped[PublicationEnvironmentTable] = relationship("PublicationEnvironmentTable")
    act: Mapped[PublicationActTable] = relationship()


class PublicationVersionTable(Base, UserMetaData):
    __tablename__ = "publication_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    publication_id: Mapped[UUID] = mapped_column(ForeignKey("publications.id"), nullable=False)
    module_status_id: Mapped[int] = mapped_column(ForeignKey("module_status_history.id"), nullable=False)

    # BesluitMetadata
    bill_metadata = Column(JSON)
    # BesluitCompact
    bill_compact = Column(JSON)
    # Procedureverloop
    procedural = Column(JSON)

    # ConsolidatieInformatie.Tijdstempels.juridischWerkendVanaf
    effective_date: Mapped[date | None]
    # opdracht-xml.datumBekendmaking
    announcement_date: Mapped[date | None]

    is_locked: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    status: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    mutation_strategy: Mapped[str] = mapped_column(Unicode(64), nullable=False, server_default="renvooi")

    publication: Mapped[PublicationTable] = relationship("PublicationTable")
    module_status: Mapped[ModuleStatusHistoryTable] = relationship("ModuleStatusHistoryTable")
    attachments: Mapped[list["PublicationVersionAttachmentTable"]] = relationship(
        back_populates="publication_version", order_by="asc(PublicationVersionAttachmentTable.id)"
    )

    act_packages: Mapped[list["PublicationActPackageTable"]] = relationship(
        back_populates="publication_version", order_by="asc(PublicationActPackageTable.created_date)"
    )


class PublicationVersionAttachmentTable(Base, UserMetaData):
    __tablename__ = "publication_version_attachments"

    # We need a small unique identifier for publications
    id: Mapped[int] = mapped_column(primary_key=True)

    publication_version_id: Mapped[UUID] = mapped_column(ForeignKey("publication_versions.id"), nullable=False)
    file_id: Mapped[UUID] = mapped_column(ForeignKey("publication_storage_files.id"), nullable=False)
    filename: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    publication_version: Mapped["PublicationVersionTable"] = relationship()
    file: Mapped[PublicationStorageFileTable] = relationship()

    __table_args__ = (UniqueConstraint("publication_version_id", "file_id", name="uix_publication_version_file"),)


class PublicationBillTable(Base, UserMetaData):
    __tablename__ = "publication_bills"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))
    document_type: Mapped[str] = mapped_column(Unicode, nullable=False)

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html#docbg
    work_province_id: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_country: Mapped[str] = mapped_column(Unicode(2), nullable=False)
    work_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_other: Mapped[str] = mapped_column(Unicode(128), nullable=False)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    __table_args__ = (UniqueConstraint("environment_id", "work_other", name="uix_pub_bil_env_other"),)


class PublicationBillVersionTable(Base):
    __tablename__ = "publication_bill_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("publication_bills.id"))

    expression_language: Mapped[str] = mapped_column(Unicode(3), nullable=False)
    expression_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    expression_version: Mapped[int] = mapped_column(Integer, nullable=False)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    bill: Mapped[PublicationBillTable] = relationship()

    __table_args__ = (UniqueConstraint("bill_id", "expression_version", name="uix_bill_version"),)


class PublicationPackageZipTable(Base):
    __tablename__ = "publication_package_zips"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    filename: Mapped[str] = mapped_column(Unicode, nullable=False)
    binary: Mapped[bytes] = deferred(mapped_column(LargeBinary(), nullable=False))
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    latest_download_date: Mapped[datetime | None]
    latest_download_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("Gebruikers.UUID"), nullable=True)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationActPackageTable(Base, UserMetaData):
    __tablename__ = "publication_act_packages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    publication_version_id: Mapped[UUID] = mapped_column(ForeignKey("publication_versions.id"), nullable=False)
    bill_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_bill_versions.id"), nullable=True)
    act_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_act_versions.id"), nullable=True)
    zip_id: Mapped[UUID] = mapped_column(ForeignKey("publication_package_zips.id"), nullable=False)

    package_type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    report_status: Mapped[str] = mapped_column(Unicode(64), nullable=False)

    delivery_id: Mapped[str] = mapped_column(String(80), nullable=False)

    used_environment_state_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("publication_environment_states.id"), nullable=True
    )
    created_environment_state_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("publication_environment_states.id"), nullable=True
    )
    module_id: Mapped[int | None] = mapped_column(ForeignKey("modules.module_id"), nullable=True)
    module_status_id: Mapped[int | None] = mapped_column(ForeignKey("module_status_history.id"), nullable=True)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    publication_version: Mapped["PublicationVersionTable"] = relationship()
    bill_version: Mapped["PublicationBillVersionTable"] = relationship()
    act_version: Mapped["PublicationActVersionTable"] = relationship()
    zip: Mapped[PublicationPackageZipTable] = relationship()
    created_environment_state: Mapped["PublicationEnvironmentStateTable"] = relationship(
        "PublicationEnvironmentStateTable",
        primaryjoin="PublicationActPackageTable.created_environment_state_id == PublicationEnvironmentStateTable.id",
    )
    module: Mapped[ModuleTable | None] = relationship("ModuleTable")
    module_status: Mapped[ModuleStatusHistoryTable | None] = relationship("ModuleStatusHistoryTable")


class PublicationActPackageReportTable(Base):
    __tablename__ = "publication_act_package_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    act_package_id: Mapped[UUID] = mapped_column(ForeignKey("publication_act_packages.id"), nullable=False)

    report_status: Mapped[str] = mapped_column(Unicode, nullable=False)

    filename: Mapped[str] = mapped_column(Unicode, nullable=False)
    source_document: Mapped[str] = mapped_column(UnicodeText)

    main_outcome: Mapped[str] = mapped_column(Unicode, nullable=False)
    sub_delivery_id: Mapped[str] = mapped_column(String(80), nullable=False)
    sub_progress: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    sub_outcome: Mapped[str] = mapped_column(Unicode(100), nullable=False)

    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationDocTable(Base, UserMetaData):
    __tablename__ = "publication_docs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("publication_environments.id"))
    document_type: Mapped[str] = mapped_column(Unicode, nullable=False)

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html#docbg
    work_province_id: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_country: Mapped[str] = mapped_column(Unicode(2), nullable=False)
    work_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    work_other: Mapped[str] = mapped_column(Unicode(128), nullable=False)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    __table_args__ = (UniqueConstraint("environment_id", "work_other", name="uix_pub_doc_env_other"),)


class PublicationDocVersionTable(Base):
    __tablename__ = "publication_doc_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("publication_docs.id"))

    expression_language: Mapped[str] = mapped_column(Unicode(3), nullable=False)
    expression_date: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    expression_version: Mapped[int] = mapped_column(Integer, nullable=False)

    created_date: Mapped[datetime]
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    doc: Mapped[PublicationDocTable] = relationship()

    __table_args__ = (UniqueConstraint("doc_id", "expression_version", name="uix_doc_version"),)


class PublicationAnnouncementTable(Base, UserMetaData):
    __tablename__ = "publication_announcements"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    # We attach an announcement to a Package as the Package has al the information
    act_package_id: Mapped[UUID] = mapped_column(ForeignKey("publication_act_packages.id"), nullable=False)
    publication_id: Mapped[UUID] = mapped_column(ForeignKey("publications.id"), nullable=False)

    meta_data = Column(JSON)
    procedural = Column(JSON)
    content = Column(JSON)

    announcement_date: Mapped[date | None]
    is_locked: Mapped[bool] = mapped_column(default=False)

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    act_package: Mapped[PublicationActPackageTable] = relationship("PublicationActPackageTable")
    publication: Mapped[PublicationTable] = relationship("PublicationTable")


class PublicationAnnouncementPackageTable(Base, UserMetaData):
    __tablename__ = "publication_announcement_packages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    announcement_id: Mapped[UUID] = mapped_column(ForeignKey("publication_announcements.id"), nullable=False)
    doc_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("publication_doc_versions.id"), nullable=True)
    zip_id: Mapped[UUID] = mapped_column(ForeignKey("publication_package_zips.id"), nullable=False)

    package_type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    report_status: Mapped[str] = mapped_column(Unicode(64), nullable=False)

    delivery_id: Mapped[str] = mapped_column(String(80), nullable=False)

    used_environment_state_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("publication_environment_states.id"), nullable=True
    )
    created_environment_state_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("publication_environment_states.id"), nullable=True
    )

    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]

    announcement: Mapped["PublicationAnnouncementTable"] = relationship()
    zip: Mapped["PublicationPackageZipTable"] = relationship()
    created_environment_state: Mapped["PublicationEnvironmentStateTable"] = relationship(
        "PublicationEnvironmentStateTable",
        primaryjoin="PublicationAnnouncementPackageTable.created_environment_state_id == PublicationEnvironmentStateTable.id",
    )


class PublicationAnnouncementPackageReportTable(Base):
    __tablename__ = "publication_announcement_package_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    announcement_package_id: Mapped[UUID] = mapped_column(
        ForeignKey("publication_announcement_packages.id"), nullable=False
    )

    report_status: Mapped[str] = mapped_column(Unicode, nullable=False)

    filename: Mapped[str] = mapped_column(Unicode, nullable=False)
    source_document: Mapped[str] = mapped_column(UnicodeText)

    main_outcome: Mapped[str] = mapped_column(Unicode, nullable=False)
    sub_delivery_id: Mapped[str] = mapped_column(String(80), nullable=False)
    sub_progress: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    sub_outcome: Mapped[str] = mapped_column(Unicode(100), nullable=False)

    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
