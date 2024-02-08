import hashlib
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String, Unicode
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.sql.expression import select

from app.core.db.base import Base
from app.core.db.mixins import TimeStamped
from app.extensions.publications.enums import IMOWTYPE, OWAssociationType, OWProcedureStatusType


def generate_hash(ow_id: str) -> str:
    if len(ow_id) <= 64:
        return ow_id

    return hashlib.sha256(ow_id.encode("utf-8")).hexdigest()


class OWAssociationTable(Base):
    """
    Generic association table for OWObject 1-to-many relationships
    """

    __tablename__ = "publication_ow_association"
    OW_ID_1_HASH = Column(String(64), ForeignKey("publication_ow_objects.OW_ID_HASH"), primary_key=True)
    OW_ID_2_HASH = Column(String(64), ForeignKey("publication_ow_objects.OW_ID_HASH"), primary_key=True)
    Type = Column(Unicode)
    # Type = Column(SQLAlchemyEnum(*[e.value for e in OWAssociationType]))

    # Relationships to ow objects
    ow_object1 = relationship("OWObjectTable", foreign_keys=[OW_ID_1_HASH])
    ow_object2 = relationship("OWObjectTable", foreign_keys=[OW_ID_2_HASH])


class OWObjectTable(Base, TimeStamped):
    __tablename__ = "publication_ow_objects"

    def __init__(self, *args, **kwargs):
        super(OWObjectTable, self).__init__(*args, **kwargs)
        if not self.OW_ID_HASH and self.OW_ID:
            self.OW_ID_HASH = generate_hash(self.OW_ID)

    UUID: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4())
    Created_Date: Mapped[datetime] = mapped_column(default=datetime.now())
    Modified_Date: Mapped[datetime] = mapped_column(default=datetime.now())

    OW_ID_HASH: Mapped[str] = mapped_column(String(64), unique=True)
    OW_ID: Mapped[str] = mapped_column(String(255))

    IMOW_Type = Column(SQLAlchemyEnum(*[e.value for e in IMOWTYPE]))
    Procedure_Status = Column(SQLAlchemyEnum(*[e.value for e in OWProcedureStatusType]))
    Noemer: Mapped[Optional[str]] = mapped_column(Unicode(255), nullable=True)

    # Relationship to PublicationPackageTable
    Package_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("publication_packages.UUID"), nullable=False)
    Package = relationship("PublicationPackageTable", back_populates="OW_Objects")

    __mapper_args__ = {
        "polymorphic_identity": "publication_ow_objects",
        "polymorphic_on": IMOW_Type,
    }


class OWDivisieTable(OWObjectTable):
    WID = Column(Unicode)

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
        primaryjoin=f"and_(OWGebiedenGroepTable.OW_ID_HASH == OWAssociationTable.OW_ID_HASH_1, OWAssociationTable.Type == '{OWAssociationType.GEBIEDENGROEP_GEBIED.value}')",
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

    Divisie_ref = Column(String(64), ForeignKey("publication_ow_objects.OW_ID_HASH"))

    # New association_proxy
    _locations = relationship(
        "OWAssociationTable",
        primaryjoin=f"and_(OWTekstdeelTable.OW_ID_HASH == OWAssociationTable.OW_ID_HASH_1, OWAssociationTable.Type == '{OWAssociationType.TEKSTDEEL_LOCATION.value}')",
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
            ow_id_hash: str = generate_hash(self.Divisie_ref)
            return session.query(OWDivisieTable).filter(OWDivisieTable.OW_ID_HASH == ow_id_hash).one_or_none()
        return None

    @divisie.expression
    def divisie(cls):
        ow_id_hash: str = generate_hash(cls.Divisie_ref)
        return select([OWDivisieTable]).where(OWDivisieTable.OW_ID_HASH == cls.Divisie_ref)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.TEKSTDEEL.value,
    }


class OWAmbtsgebiedTable(OWObjectTable):
    Bestuurlijke_grenzen_id: Mapped[str] = mapped_column(Unicode(255), nullable=True)
    Domein: Mapped[str] = mapped_column(Unicode(255), nullable=True)
    Geldig_Op: Mapped[str] = mapped_column(Unicode(255), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.AMBTSGEBIED.value,
    }


class OWRegelingsgebiedTable(OWObjectTable):
    Ambtsgebied: Mapped[str] = mapped_column(Unicode(255), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": IMOWTYPE.REGELINGSGEBIED.value,
    }
