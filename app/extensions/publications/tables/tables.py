from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Column, String, UniqueConstraint, func, Enum as SQLAlchemyEnum
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Integer, JSON


from app.core.db.base import Base
from app.core.db.mixins import HasUUID, TimeStamped
from app.extensions.publications.enums import IMOWTYPE, Document_Type, Package_Event_Type, Bill_Type


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
    __tablename__ = "publication_bill"
    __table_args__ = (UniqueConstraint("Module_ID", "Document_Type", "Version_ID"),)

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    Created_Date: Mapped[Optional[datetime]]
    Modified_Date: Mapped[Optional[datetime]]

    Version_ID: Mapped[int]
    Module_ID: Mapped[int] = mapped_column(Integer, ForeignKey("modules.Module_ID"), nullable=False)
    Module_Status_ID: Mapped[int] = mapped_column(
        Integer, ForeignKey("module_status_history.ID"), nullable=False
    )
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
        return (
            db.query(func.max(cls.Version_ID))
            .filter_by(Module_ID=module_id, Document_Type=document_type)
            .scalar()
        )

    @hybrid_method
    def next_version(cls, db, module_id, document_type) -> int:
        latest = cls.latest_version(db, module_id, document_type)
        if not latest:
            return 1
        return latest + 1


class PublicationPackageTable(Base, HasUUID, TimeStamped):
    __tablename__ = "publication_package"

    # the leveringId == PublicationPackageTable.UUID
    Bill_UUID: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publication_bill.UUID"), nullable=False
    )
    Package_Event_Type = Column(SQLAlchemyEnum(*[e.value for e in Package_Event_Type]))
    Publication_Filename: Mapped[Optional[str]]  # Publicatie_Bestandnaam
    Announcement_Date: Mapped[Optional[datetime]]  # Datum_Bekendmaking

    # Stamped publication config at the time of packaging
    Province_ID: Mapped[str]   # Provincie_ID
    Submitter_ID: Mapped[int]  # Id_Aanleveraar
    Authority_ID: Mapped[int]  # Id_Bevoegdgezag
    Jurisdiction: Mapped[str]  # Rechtsgebied
    Subjects: Mapped[str]      # Onderwerpen
    dso_stop_version: Mapped[str]
    dso_tpod_version: Mapped[str]
    dso_bhkv_version: Mapped[str]

    ow_objects = relationship("OWObject", back_populates="Package")
