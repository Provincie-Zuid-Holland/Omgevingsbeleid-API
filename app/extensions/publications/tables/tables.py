import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, LargeBinary, Text, Unicode, UniqueConstraint
from sqlalchemy.orm import Mapped, backref, deferred, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, Integer

from app.core.db.base import Base
from app.core.db.mixins import HasUUID, TimeStamped, UserMetaData
from app.extensions.publications.enums import DocumentType, PackageEventType, ProcedureType, ValidationStatusType
from app.extensions.publications.tables.ow import package_ow_association


class PublicationConfigTable(Base):
    __tablename__ = "publication_config"

    ID: Mapped[int] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]

    Province_ID: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Provincie_ID
    Authority_ID: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Bevoegdgezag_ID
    Submitter_ID: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Aanleveraar_ID
    Jurisdiction: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Rechtsgebied
    Subjects: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Onderwerpen
    Governing_Body_Type: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Bestuursorgaan_Soort
    Act_Componentname: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # Regeling Componentnaam

    Administrative_Borders_ID: Mapped[str] = mapped_column(Unicode(255), nullable=False)  # bestuurlijke grenzen ID
    Administrative_Borders_Domain: Mapped[str] = mapped_column(
        Unicode(255), nullable=False
    )  # bestuurlijke grenzen domein
    Administrative_Borders_Date: Mapped[date] = mapped_column(Date, nullable=False)  # bestuurlijke grenzen bekend op

    DSO_STOP_VERSION: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    DSO_TPOD_VERSION: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    DSO_BHKV_VERSION: Mapped[str] = mapped_column(Unicode(255), nullable=False)


class PublicationTable(Base, HasUUID, TimeStamped, UserMetaData):
    __tablename__ = "publications"
    __table_args__ = (UniqueConstraint("Document_Type", "Work_ID", name="uq_publications_document_work"),)

    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Modified_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Module_ID: Mapped[int] = mapped_column(Integer, ForeignKey("modules.Module_ID"), nullable=False)
    Template_ID: Mapped[Optional[int]]  # TODO: key to new template storage

    Document_Type = Column(SQLAlchemyEnum(*[e.value for e in DocumentType]))
    Work_ID: Mapped[int]  # FRBR counter

    Official_Title: Mapped[str] = mapped_column(Unicode(), nullable=False)  # Officiele titel
    Regulation_Title: Mapped[str] = mapped_column(Unicode(), nullable=False)  # Regeling opschrift

    Module: Mapped["ModuleTable"] = relationship("ModuleTable")


class PublicationBillTable(Base, HasUUID, TimeStamped, UserMetaData):
    __tablename__ = "publication_bills"

    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Modified_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Publication_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.UUID"), nullable=False)
    Module_Status_ID: Mapped[int] = mapped_column(Integer, ForeignKey("module_status_history.ID"), nullable=False)
    Version_ID: Mapped[int]

    Is_Official: Mapped[bool]
    Procedure_Type = Column(SQLAlchemyEnum(*[e.value for e in ProcedureType]), nullable=False)  # Procedure soort
    Bill_Data = Column(JSON)  # Besluit
    Procedure_Data = Column(JSON)  # Procedureverloop
    Effective_Date: Mapped[Optional[date]]  # Juridische inwerkingtredingsdatum
    Announcement_Date: Mapped[Optional[date]]  # Bekendmaking_Datum
    PZH_Bill_Identifier: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)  # Besluitnummer
    Locked: Mapped[bool] = mapped_column(default=False)

    Publication: Mapped["PublicationTable"] = relationship("PublicationTable")
    Module_Status: Mapped["ModuleStatusHistoryTable"] = relationship("ModuleStatusHistoryTable")
    Packages: Mapped[List["PublicationPackageTable"]] = relationship(
        "PublicationPackageTable", backref="publication_bill"
    )


class PublicationFRBRTable(Base):
    __tablename__ = "publication_frbr"
    __table_args__ = (
        UniqueConstraint("bill_work_misc", "bill_expression_version", name="bill_unique_constraint"),
        UniqueConstraint("act_work_misc", "act_expression_version", name="act_unique_constraint"),
    )

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Fields for bill_frbr
    bill_work_country: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    bill_work_date: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    bill_work_misc: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    bill_expression_lang: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    bill_expression_date: Mapped[date]
    bill_expression_version: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    bill_expression_misc: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)

    # Fields for act_frbr
    act_work_country: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    act_work_date: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    act_work_misc: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    act_expression_lang: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    act_expression_date: Mapped[date]
    act_expression_version: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    act_expression_misc: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)

    @classmethod
    def create_default_frbr(
        cls,
        document_type: str,
        work_ID: int,
        expression_version: int,
    ):
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%Y-%m-%d")
        return cls(
            Created_Date=datetime.now(),
            bill_work_country="nl",
            bill_work_date=str(current_year),
            bill_work_misc=f"{document_type}_{work_ID}",
            bill_expression_lang="nld",
            bill_expression_date=current_date,
            bill_expression_version=str(expression_version),
            act_work_country="nl",
            act_work_date=str(current_year),
            act_work_misc=f"{document_type}_{work_ID}",
            act_expression_lang="nld",
            act_expression_date=current_date,
            act_expression_version=str(expression_version),
        )


class PublicationPackageTable(Base, HasUUID, UserMetaData):
    __tablename__ = "publication_packages"
    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Modified_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Latest_Download_Date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    Latest_Download_By_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Gebruikers.UUID"), nullable=True)

    Bill_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_bills.UUID"), nullable=False)
    Config_ID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_config.ID"), nullable=False)
    FRBR_ID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_frbr.ID"), nullable=False)

    Package_Event_Type = Column(SQLAlchemyEnum(*[e.value for e in PackageEventType]), nullable=False)
    Publication_Filename: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)  # Publicatie_Bestandnaam
    Announcement_Date: Mapped[date]  # Datum_Bekendmaking

    ZIP_File_Name: Mapped[Optional[str]] = mapped_column(Unicode, nullable=True)
    ZIP_File_Binary: Mapped[Optional[bytes]] = deferred(Column(LargeBinary))  # Change to azure blob storage later
    ZIP_File_Checksum: Mapped[Optional[str]] = Column(Unicode(64))

    Validation_Status = Column(
        SQLAlchemyEnum(*[e.value for e in ValidationStatusType]),
        nullable=False,
        default=ValidationStatusType.PENDING.value,
    )

    Config: Mapped["PublicationConfigTable"] = relationship("PublicationConfigTable")
    Bill: Mapped["PublicationBillTable"] = relationship("PublicationBillTable")
    FRBR_Info: Mapped["PublicationFRBRTable"] = relationship(
        "PublicationFRBRTable",
        backref=backref("publication_package", uselist=False, cascade="all, delete-orphan"),
    )
    Reports: Mapped[List["PublicationPackageReportTable"]] = relationship(
        "PublicationPackageReportTable", back_populates="Package"
    )
    OW_Objects: Mapped[List["OWObjectTable"]] = relationship(
        "OWObjectTable", secondary=package_ow_association, back_populates="Packages"
    )


class PublicationPackageReportTable(Base):
    __tablename__ = "publication_package_reports"

    ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Created_Date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))

    Package_UUID: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publication_packages.UUID"), nullable=False
    )  # Idlevering
    Result: Mapped[str] = mapped_column(Unicode, nullable=False)  # Uitkomst
    Report_Timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # tijdstipVerslag
    Messages = Column(Text)  # Storing XML string of <meldingen> for simplicity
    Source_Document = Column(Text)  # full original document for downloading
    Report_Type: Mapped[str] = mapped_column(Unicode, nullable=False)  # Voortgang

    Package = relationship("PublicationPackageTable", back_populates="Reports")


class DSOStateExportTable(Base, HasUUID):
    __tablename__ = "publication_dso_state_exports"

    Created_Date: Mapped[datetime]
    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Export_Data = Column(JSON)
