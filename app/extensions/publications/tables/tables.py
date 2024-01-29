import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.sql.sqltypes import JSON, Integer

from app.core.db.base import Base
from app.core.db.mixins import HasUUID, TimeStamped
from app.extensions.publications.enums import Bill_Type, Document_Type, Package_Event_Type


class PublicationConfigTable(Base):
    __tablename__ = "publication_config"

    ID: Mapped[int] = mapped_column(primary_key=True)
    Created_Date: Mapped[datetime]
    Modified_Date: Mapped[datetime]

    Province_ID: Mapped[str]  # Provincie_ID
    Authority_ID: Mapped[str]  # Bevoegdgezag_ID
    Submitter_ID: Mapped[str]  # Aanleveraar_ID
    Jurisdiction: Mapped[str]  # Rechtsgebied
    Subjects: Mapped[str]  # Onderwerpen

    dso_stop_version: Mapped[str]
    dso_tpod_version: Mapped[str]
    dso_bhkv_version: Mapped[str]


class PublicationBillTable(Base):
    __tablename__ = "publication_bills"
    __table_args__ = (UniqueConstraint("Module_ID", "Document_Type", "Version_ID"),)

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[Optional[datetime]]
    Modified_Date: Mapped[Optional[datetime]]

    Version_ID: Mapped[int]
    Module_ID: Mapped[int] = mapped_column(Integer, ForeignKey("modules.Module_ID"), nullable=False)
    Module_Status_ID: Mapped[int] = mapped_column(Integer, ForeignKey("module_status_history.ID"), nullable=False)
    Bill_Type = Column(SQLAlchemyEnum(*[e.value for e in Bill_Type]))
    Document_Type = Column(SQLAlchemyEnum(*[e.value for e in Document_Type]))
    Bill_Data = Column(JSON)  # Besluit
    Procedure_Data = Column(JSON)  # Procedureverloop
    Council_Proposal_File: Mapped[Optional[str]]  # Statenvoorstel_Bestand
    Effective_Date: Mapped[Optional[datetime]]  # Juridische inwerkingtredingsdatum
    Announcement_Date: Mapped[Optional[datetime]]  # Bekendmaking_Datum

    Module: Mapped["ModuleTable"] = relationship("ModuleTable")
    Module_Status: Mapped["ModuleStatusHistoryTable"] = relationship("ModuleStatusHistoryTable")

    Packages: Mapped[List["PublicationPackageTable"]] = relationship(
        "PublicationPackageTable", backref="publication_bill"
    )

    @hybrid_method
    def latest_version(cls, db, module_id, document_type):
        return db.query(func.max(cls.Version_ID)).filter_by(Module_ID=module_id, Document_Type=document_type).scalar()

    @hybrid_method
    def next_version(cls, db, module_id, document_type) -> int:
        latest = cls.latest_version(db, module_id, document_type)
        if not latest:
            return 1
        return latest + 1


class PublicationFRBRTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_frbr"

    # Fields for bill_frbr
    bill_work_country: Mapped[str]  # work_land
    bill_work_date: Mapped[str]  # work_datum
    bill_work_misc: Mapped[Optional[str]]  # work_overig
    bill_expression_lang: Mapped[str]  # expression_taal
    bill_expression_date: Mapped[datetime]  # expression_datum
    bill_expression_version: Mapped[str]  # expression_versie
    bill_expression_misc: Mapped[Optional[str]]  # expression_overig

    # Fields for act_frbr
    act_work_country: Mapped[str]  # work_land
    act_work_date: Mapped[str]  # work_datum
    act_work_misc: Mapped[Optional[str]]  # work_overig
    act_expression_lang: Mapped[str]  # expression_taal
    act_expression_date: Mapped[datetime]  # expression_datum
    act_expression_version: Mapped[str]  # expression_versie
    act_expression_misc: Mapped[Optional[str]]  # expression_overig

    @classmethod
    def create_default(cls, session, document_type: str):
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%Y-%m-%d")
        next_bill_expression_version = cls.get_next_expression_version(session, "bill")
        next_act_expression_version = cls.get_next_expression_version(session, "act")

        return cls(
            UUID=uuid.uuid4(),
            Created_Date=current_date,
            Modified_Date=current_date,
            # Fields for bill_frbr
            bill_work_country="nl",
            bill_work_date=str(current_year),
            bill_work_misc=f"{document_type}_{next_bill_expression_version}",
            bill_expression_lang="nld",
            bill_expression_date=current_date,
            bill_expression_version=str(next_bill_expression_version),
            bill_expression_misc=None,
            # Fields for act_frbr
            act_work_country="nl",
            act_work_date=str(current_year),
            act_work_misc=f"{document_type}_{next_act_expression_version}",
            act_expression_lang="nld",
            act_expression_date=current_date,
            act_expression_version=str(next_act_expression_version),
            act_expression_misc=None,
        )

    @classmethod
    def get_next_expression_version(cls, session, type):
        max_version_query = session.query(
            func.max(
                cls.bill_expression_version.cast(Integer)
                if type == "bill"
                else cls.act_expression_version.cast(Integer)
            )
        )
        max_version = max_version_query.scalar() or 0
        next_version = max_version + 1
        return str(next_version)


class PublicationPackageTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_packages"

    # the leveringId == PublicationPackageTable.UUID
    Bill_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_bills.UUID"), nullable=False)
    Package_Event_Type = Column(SQLAlchemyEnum(*[e.value for e in Package_Event_Type]))
    Publication_Filename: Mapped[Optional[str]]  # Publicatie_Bestandnaam
    Announcement_Date: Mapped[Optional[datetime]]  # Datum_Bekendmaking
    validated_at: Mapped[Optional[datetime]]  # Validated date

    # Stamped publication config at the time of packaging
    Province_ID: Mapped[str]  # Provincie_ID
    Submitter_ID: Mapped[str]  # Id_Aanleveraar
    Authority_ID: Mapped[str]  # Id_Bevoegdgezag
    Jurisdiction: Mapped[str]  # Rechtsgebied
    Subjects: Mapped[str]  # Onderwerpen
    dso_stop_version: Mapped[str]
    dso_tpod_version: Mapped[str]
    dso_bhkv_version: Mapped[str]

    # Foreign key to PublicationFRBRTable
    frbr_uuid: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_frbr.UUID"), nullable=False, unique=True)

    # Relationship to PublicationFRBRTable
    frbr_info: Mapped["PublicationFRBRTable"] = relationship(
        "PublicationFRBRTable", backref=backref("publication_package", uselist=False, cascade="all, delete-orphan")
    )

    ow_objects = relationship("OWObjectTable", back_populates="Package")


class DSOStateExportTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_dso_state_exports"

    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Export_Data = Column(JSON)
