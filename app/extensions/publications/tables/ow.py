from datetime import datetime
import uuid
from git import Optional
from sqlalchemy import Column, String, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.sql.expression import select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session

from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.db.base import Base
from app.core.db.mixins import HasUUID, TimeStamped

from app.extensions.publications.enums import IMOWTYPE, OWProcedureStatus, OWAssociationType


class OWAssociation(Base):
    """
    Generic association table for OWObject 1-to-many relationships
    """
    __tablename__ = "publication_ow_association"
    OW_ID_1 = Column(String, ForeignKey("publication_ow_objects.OW_ID"), primary_key=True)
    OW_ID_2 = Column(String, ForeignKey("publication_ow_objects.OW_ID"), primary_key=True)
    Type = Column(String)
    # Type = Column(SQLAlchemyEnum(*[e.value for e in OWAssociationType]))


class OWObject(Base, TimeStamped):
    __tablename__ = "publication_ow_objects"

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4())
    Created_Date: Mapped[Optional[datetime]] = mapped_column(default=datetime.now())
    Modified_Date: Mapped[Optional[datetime]] = mapped_column(default=datetime.now())

    OW_ID = Column(String, primary_key=True)
    IMOW_Type = Column(SQLAlchemyEnum(*[e.value for e in IMOWTYPE]))
    Procedure_Status = Column(SQLAlchemyEnum(*[e.value for e in OWProcedureStatus]))
    Noemer: Mapped[Optional[str]]

    # Relationship to PublicationPackageTable
    Package_UUID: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publication_package.UUID"), nullable=False
    )
    Package = relationship("PublicationPackageTable", back_populates="ow_objects")

    __mapper_args__ = {
        "polymorphic_identity": "publication_ow_objects",
        "polymorphic_on": IMOW_Type,
    }


class OWDivisie(OWObject):
    WID = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.DIVISIE.value,
    }


class OWDivisietekst(OWDivisie):
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.DIVISIETEKST.value,
    }


class OWLocation(OWObject):
    Geo_UUID: Mapped[Optional[uuid.UUID]]  # TODO: foreignkey to werkingsgebied


class OWGebied(OWLocation):
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.GEBIED.value,
    }


class OWGebiedenGroep(OWLocation):
    Gebieden = relationship(
        "OWGebied",
        secondary="publication_ow_association",
        primaryjoin=f"and_(OWGebiedenGroep.OW_ID == OWAssociation.OW_ID_1, OWAssociation.Type == '{OWAssociationType.GEBIEDENGROEP_GEBIED.value}')",
        secondaryjoin=(OWObject.OW_ID == OWAssociation.OW_ID_2),
    )

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.GEBIEDENGROEP.value,
    }


class OWTekstdeel(OWObject):
    Divisie_ref = Column(String, ForeignKey("publication_ow_objects.OW_ID"))

    Locations = relationship(
        "OWLocation",
        secondary="publication_ow_association",
        primaryjoin=f"and_(OWTekstdeel.OW_ID == OWAssociation.OW_ID_1, OWAssociation.Type == '{OWAssociationType.TEKSTDEEL_LOCATION.value}')",
        secondaryjoin=(OWObject.OW_ID == OWAssociation.OW_ID_2),
    )

    @hybrid_property
    def divisie(self):
        if self.Divisie_ref:
            session = Session.object_session(self)
            return (
                session.query(OWDivisie).filter(OWDivisie.OW_ID == self.Divisie_ref).one_or_none()
            )
        return None

    @divisie.expression
    def divisie(cls):
        return select([OWDivisie]).where(OWDivisie.OW_ID == cls.Divisie_ref)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.TEKSTDEEL.value,
    }


class OWAmbtsgebied(OWObject):
    Bestuurlijke_grenzen_id = Column(String)
    Domein = Column(String)
    Geldig_Op = Column(String)
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.AMBTSGEBIED.value,
    }


class OWRegelingsgebied(OWObject):
    Ambtsgebied = Column(String)
    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.REGELINGSGEBIED.value,
    }
