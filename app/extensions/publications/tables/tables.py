import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, LargeBinary, String, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, Integer

from app.core.db.base import Base
from app.core.db.mixins import UserMetaData
from app.extensions.modules.db.tables import ModuleStatusHistoryTable


class PublicationTemplateTable(Base, UserMetaData):
    __tablename__ = "publication_templates"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Title: Mapped[str] = mapped_column(Unicode, nullable=False)
    Description: Mapped[str] = mapped_column(Unicode, nullable=False)

    Is_Active: Mapped[bool]
    Document_Type: Mapped[str] = mapped_column(Unicode, nullable=False)
    Object_Types: Mapped[list] = mapped_column(JSON, nullable=False)
    Text_Template: Mapped[str] = mapped_column(Unicode, nullable=False)
    Object_Templates: Mapped[dict] = mapped_column(JSON, nullable=False)
    Field_Map: Mapped[list] = mapped_column(JSON, nullable=False)

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]


class PublicationEnvironmentTable(Base, UserMetaData):
    __tablename__ = "publication_environments"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Title: Mapped[str] = mapped_column(Unicode)
    Description: Mapped[str] = mapped_column(Unicode)

    Province_ID: Mapped[str] = mapped_column(Unicode(32), nullable=False)
    Authority_ID: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    Submitter_ID: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    Governing_Body_Type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    Frbr_Country: Mapped[str] = mapped_column(Unicode(2), nullable=False)
    Frbr_Language: Mapped[str] = mapped_column(Unicode(3), nullable=False)

    Is_Active: Mapped[bool]
    Has_State: Mapped[bool]
    Can_Validate: Mapped[bool]
    Can_Publicate: Mapped[bool]

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]


class PublicationEnvironmentStateTable(Base):
    __tablename__ = "publication_environment_states"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Environment_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_environments.UUID"))
    Adjust_On_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("publication_environment_states.UUID"), nullable=True
    )

    Change_Set = Column(JSON)
    State = Column(JSON)

    Is_Activated: Mapped[bool]
    Activated_Datetime: Mapped[Optional[datetime]]

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationAreaOfJurisdictionTable(Base):
    # Ambtsgebied
    __tablename__ = "publication_area_of_jurisdictions"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Administrative_Borders_ID: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    Administrative_Borders_Domain: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    Administrative_Borders_Date: Mapped[date] = mapped_column(Date, nullable=False)

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationTable(Base, UserMetaData):
    __tablename__ = "publications"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Module_ID: Mapped[int] = mapped_column(Integer, ForeignKey("modules.Module_ID"), nullable=False)
    Document_Type: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    Template_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_templates.UUID"), nullable=False)

    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Modified_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Module: Mapped["ModuleTable"] = relationship("ModuleTable")
    Template: Mapped["PublicationTemplateTable"] = relationship("PublicationTemplateTable")


class PublicationVersionTable(Base, UserMetaData):
    __tablename__ = "publication_versions"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Publication_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.UUID"), nullable=False)
    Module_Status_ID: Mapped[int] = mapped_column(ForeignKey("module_status_history.ID"), nullable=False)
    Environment_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_environments.UUID"))
    Procedure_Type: Mapped[str] = mapped_column(Unicode(50), nullable=False)

    # BesluitMetadata
    Bill_Metadata = Column(JSON)
    # BesluitCompact
    Bill_Compact = Column(JSON)
    # Procedureverloop
    Procedural = Column(JSON)
    # RegelingMetadata
    Act_Metadata = Column(JSON)

    # ConsolidatieInformatie.Tijdstempels.juridischWerkendVanaf
    Effective_Date: Mapped[Optional[date]]
    # opdracht-xml.datumBekendmaking
    Announcement_Date: Mapped[Optional[date]]

    Locked: Mapped[bool] = mapped_column(default=False)

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Publication: Mapped[PublicationTable] = relationship("PublicationTable")
    Module_Status: Mapped[ModuleStatusHistoryTable] = relationship("ModuleStatusHistoryTable")
    Environment: Mapped[PublicationEnvironmentTable] = relationship("PublicationEnvironmentTable")
    # Packages: Mapped[List["PublicationPackageTable"]] = relationship(back_populates="Bill")


class PublicationActTable(Base, UserMetaData):
    __tablename__ = "publication_acts"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Environment_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_environments.UUID"))

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html#docbg
    Work_Other: Mapped[str] = mapped_column(Unicode(128), nullable=False, unique=True)
    Status: Mapped[str]

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]


class PublicationActVersionTable(Base, UserMetaData):
    __tablename__ = "publication_act_versions"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Act_UUID: Mapped[int] = mapped_column(ForeignKey("publication_acts.UUID"))
    Version: Mapped[int] = mapped_column(Integer, nullable=False)

    Act: Mapped[PublicationActTable] = relationship()

    __table_args__ = (UniqueConstraint("Act_UUID", "Version", name="uix_act_version"),)


class PublicationBillTable(Base, UserMetaData):
    __tablename__ = "publication_bills"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Environment_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_environments.UUID"))

    # @see: https://koop.gitlab.io/STOP/standaard/1.3.0/identificatie_doc_pub.html#docbg
    Work_Other: Mapped[str] = mapped_column(Unicode(128), nullable=False, unique=True)
    Status: Mapped[str]

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]


class PublicationBillVersionTable(Base, UserMetaData):
    __tablename__ = "publication_bill_versions"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Bill_UUID: Mapped[int] = mapped_column(ForeignKey("publication_bills.UUID"))
    Version: Mapped[int] = mapped_column(Integer, nullable=False)

    Bill: Mapped[PublicationBillTable] = relationship()

    __table_args__ = (UniqueConstraint("Bill_UUID", "Version", name="uix_bill_version"),)


class PublicationPackageTable(Base, UserMetaData):
    __tablename__ = "publication_packages"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Publication_Version_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_versions.UUID"), nullable=False)
    Bill_Version_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("publication_bill_versions.UUID"), nullable=True
    )
    Act_Version_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("publication_act_versions.UUID"), nullable=True
    )
    Zip_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_package_zips.UUID"), nullable=False)

    Package_Type: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    Validation_Status: Mapped[str] = mapped_column(Unicode(64), nullable=False)

    Delivery_ID: Mapped[str] = mapped_column(String(80), nullable=False)

    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Publication_Version: Mapped["PublicationVersionTable"] = relationship()


class PublicationPackageZipTable(Base):
    __tablename__ = "publication_package_zips"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Filename: Mapped[str] = mapped_column(Unicode, nullable=False)
    Binary: Mapped[bytes] = deferred(mapped_column(LargeBinary(), nullable=False))
    Checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    Latest_Download_Date: Mapped[Optional[datetime]]
    Latest_Download_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"), nullable=True)

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class PublicationPackageReportTable(Base):
    __tablename__ = "publication_package_reports"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)

    Outcome: Mapped[str] = mapped_column(Unicode, nullable=False)
    Result: Mapped[str] = mapped_column(Unicode, nullable=False)
    Report_Timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Messages: Mapped[str] = mapped_column(UnicodeText)
    Report_Progress: Mapped[str] = mapped_column(Unicode, nullable=True)

    Filename: Mapped[str] = mapped_column(Unicode, nullable=False)
    Source_Document: Mapped[str] = mapped_column(UnicodeText)


class PublicationPackageExportState(Base):
    __tablename__ = "publication_package_export_state"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Export_Data = Column(JSON)

    Created_Date: Mapped[datetime]
