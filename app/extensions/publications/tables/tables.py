import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, Integer

from app.core.db.base import Base
from app.core.db.mixins import HasUUID, TimeStamped
from app.extensions.publications.enums import Document_Type, Package_Event_Type, Procedure_Type


class PublicationConfigTable(Base):
    __tablename__ = "publication_config"

    ID: Mapped[int] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]

    Province_ID: Mapped[str]  # Provincie_ID
    Authority_ID: Mapped[str]  # Bevoegdgezag_ID
    Submitter_ID: Mapped[str]  # Aanleveraar_ID
    Jurisdiction: Mapped[str]  # Rechtsgebied
    Subjects: Mapped[str]  # Onderwerpen
    # Act_Componentname: Mapped[str]  # Regeling Componentnaam

    DSO_STOP_VERSION: Mapped[str]
    DSO_TPOD_VERSION: Mapped[str]
    DSO_BHKV_VERSION: Mapped[str]


class PublicationTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publications"
    __table_args__ = (UniqueConstraint("Document_Type", "Work_ID", name="uq_publications_document_work"),)

    Module_ID: Mapped[int] = mapped_column(Integer, ForeignKey("modules.Module_ID"), nullable=False)
    Template_ID: Mapped[Optional[int]]  # TODO: key to new template storage

    Document_Type = Column(SQLAlchemyEnum(*[e.value for e in Document_Type]))
    Work_ID: Mapped[int]  # FRBR counter

    Official_Title: Mapped[str]  # Officiele titelb
    Regulation_Title: Mapped[str]  # Regeling opschrift

    Module: Mapped["ModuleTable"] = relationship("ModuleTable")


class PublicationBillTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_bills"

    Publication_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.UUID"), nullable=False)
    Module_Status_ID: Mapped[int] = mapped_column(Integer, ForeignKey("module_status_history.ID"), nullable=False)

    Version_ID: Mapped[int]

    Is_Official: Mapped[bool]
    Procedure_Type = Column(SQLAlchemyEnum(*[e.value for e in Procedure_Type]), nullable=False)  # Procedure soort
    Bill_Data = Column(JSON)  # Besluit
    Procedure_Data = Column(JSON)  # Procedureverloop
    Effective_Date: Mapped[Optional[datetime]]  # Juridische inwerkingtredingsdatum
    Announcement_Date: Mapped[Optional[datetime]]  # Bekendmaking_Datum
    # Council_Proposal_File: Mapped[Optional[str]]  # Statenvoorstel_Bestand

    # TODO: Add titles to allow overrride from PublicationTable?

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
    bill_work_country: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_work_date: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_work_misc: Mapped[str] = mapped_column(String(255), nullable=True)
    bill_expression_lang: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_expression_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bill_expression_version: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_expression_misc: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

    # Fields for act_frbr
    act_work_country: Mapped[str] = mapped_column(String(255), nullable=False)
    act_work_date: Mapped[str] = mapped_column(String(255), nullable=False)
    act_work_misc: Mapped[str] = mapped_column(String(255), nullable=True)
    act_expression_lang: Mapped[str] = mapped_column(String(255), nullable=False)
    act_expression_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    act_expression_version: Mapped[str] = mapped_column(String(255), nullable=False)
    act_expression_misc: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)

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


class PublicationPackageTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_packages"

    Bill_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_bills.UUID"), nullable=False)
    Config_ID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_config.ID"), nullable=False)
    FRBR_ID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_frbr.ID"), nullable=False, unique=True)

    Package_Event_Type = Column(SQLAlchemyEnum(*[e.value for e in Package_Event_Type]))
    Publication_Filename: Mapped[Optional[str]]  # Publicatie_Bestandnaam
    Announcement_Date: Mapped[Optional[datetime]]  # Datum_Bekendmaking
    Validated_At: Mapped[Optional[datetime]]  # Validated date
    # Validation_Report: Mapped[Optional[str]]  # LVBB Validatie resultaat

    Config: Mapped["PublicationConfigTable"] = relationship("PublicationConfigTable")
    Bill: Mapped["PublicationBillTable"] = relationship("PublicationBillTable")
    FRBR_Info: Mapped["PublicationFRBRTable"] = relationship(
        "PublicationFRBRTable", backref=backref("publication_package", uselist=False, cascade="all, delete-orphan")
    )
    OW_Objects: Mapped[List["OWObjectTable"]] = relationship("OWObjectTable", back_populates="Package")


class DSOStateExportTable(Base, HasUUID):
    __tablename__ = "publication_dso_state_exports"

    Created_Date: Mapped[datetime]
    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Export_Data = Column(JSON)
