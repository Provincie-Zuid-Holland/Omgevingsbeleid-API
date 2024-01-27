import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.sql.expression import select

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped
from app.extensions.publications.enums import IMOWTYPE, OWAssociationType, OWProcedureStatus


class OWAssociationTable(Base):
    """
    Generic association table for OWObject 1-to-many relationships
    """

    __tablename__ = "publication_ow_association"
    OW_ID_1 = Column(String(255), ForeignKey("publication_ow_objects.OW_ID"), primary_key=True)
    OW_ID_2 = Column(String(255), ForeignKey("publication_ow_objects.OW_ID"), primary_key=True)
    Type = Column(String)
    # Type = Column(SQLAlchemyEnum(*[e.value for e in OWAssociationType]))

    # Relationships to ow objects
    ow_object1 = relationship("OWObjectTable", foreign_keys=[OW_ID_1])
    ow_object2 = relationship("OWObjectTable", foreign_keys=[OW_ID_2])


class OWObjectTable(Base, TimeStamped):
    __tablename__ = "publication_ow_objects"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4())
    Created_Date: Mapped[datetime] = mapped_column(default=datetime.now())
    Modified_Date: Mapped[datetime] = mapped_column(default=datetime.now())

    OW_ID: Mapped[str] = mapped_column(String(255), unique=True)

    IMOW_Type = Column(SQLAlchemyEnum(*[e.value for e in IMOWTYPE]))
    Procedure_Status = Column(SQLAlchemyEnum(*[e.value for e in OWProcedureStatus]))
    Noemer: Mapped[Optional[str]]

    # Relationship to PublicationPackageTable
    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Package = relationship("PublicationPackageTable", back_populates="ow_objects")

    __mapper_args__ = {
        "polymorphic_identity": "publication_ow_objects",
        "polymorphic_on": IMOW_Type,
    }


class OWDivisieTable(OWObjectTable):
    WID = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.DIVISIE.value,
    }


class OWDivisietekstTable(OWDivisieTable):
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.DIVISIETEKST.value,
    }


class OWLocationTable(OWObjectTable):
    Geo_UUID: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("Werkingsgebieden.UUID"), nullable=True)

    __mapper_args__ = {
        "polymorphic_abstract": True,
    }


class OWGebiedTable(OWLocationTable):
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.GEBIED.value,
    }


class OWGebiedenGroepTable(OWLocationTable):
    # Relationship using OWAssociationTable
    _gebieden = relationship(
        "OWAssociationTable",
        primaryjoin=f"and_(OWGebiedenGroepTable.OW_ID == OWAssociationTable.OW_ID_1, OWAssociationTable.Type == '{OWAssociationType.GEBIEDENGROEP_GEBIED.value}')",
        cascade="all, delete-orphan",
    )

    Gebieden = association_proxy(
        "_gebieden",
        "ow_object2",
        creator=lambda ow_object2: OWAssociationTable(
            ow_object2=ow_object2, Type=OWAssociationType.GEBIEDENGROEP_GEBIED.value
        ),
    )

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.GEBIEDENGROEP.value,
    }


class OWTekstdeelTable(OWObjectTable):
    """
    Tekstdeel maps the tekst divs to the locations, and it has a 1-to-many relationship with OWLocationTable.
    the association proxy is used to auto insert the correct OWAssociation with matching type.
    """

    Divisie_ref = Column(String(255), ForeignKey("publication_ow_objects.OW_ID"))

    # New association_proxy
    _locations = relationship(
        "OWAssociationTable",
        primaryjoin=f"and_(OWTekstdeelTable.OW_ID == OWAssociationTable.OW_ID_1, OWAssociationTable.Type == '{OWAssociationType.TEKSTDEEL_LOCATION.value}')",
        cascade="all, delete-orphan",
    )

    Locations = association_proxy(
        "_locations",
        "ow_object2",
        creator=lambda ow_object2: OWAssociationTable(
            ow_object2=ow_object2, Type=OWAssociationType.TEKSTDEEL_LOCATION.value
        ),
    )

    @hybrid_property
    def divisie(self):
        if self.Divisie_ref:
            session = Session.object_session(self)
            return session.query(OWDivisieTable).filter(OWDivisieTable.OW_ID == self.Divisie_ref).one_or_none()
        return None

    @divisie.expression
    def divisie(cls):
        return select([OWDivisieTable]).where(OWDivisieTable.OW_ID == cls.Divisie_ref)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.TEKSTDEEL.value,
    }


class OWAmbtsgebiedTable(OWObjectTable):
    Bestuurlijke_grenzen_id: Mapped[str]
    Domein: Mapped[str]
    Geldig_Op: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.AMBTSGEBIED.value,
    }


class OWRegelingsgebiedTable(OWObjectTable):
    Ambtsgebied: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.REGELINGSGEBIED.value,
    }
