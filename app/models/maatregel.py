from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    text,
    DateTime,
    Unicode,
    Sequence,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401
    from .maatregel import Maatregel  # noqa: F401


class Beleidskeuze_Maatregelen(Base):
    __tablename__ = "Beleidskeuze_Maatregelen"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Maatregelen")
    Maatregel = relationship("Maatregel", back_populates="Beleidskeuzes")


class Beleidsmodule_Maatregelen(Base):
    __tablename__ = "Beleidsmodule_Maatregelen"

    Beleidsmodule_UUID = Column(ForeignKey("Beleidsmodules.UUID"), primary_key=True)
    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidsmodule = relationship("Beleidsmodule", back_populates="Maatregelen")
    Maatregel = relationship("Maatregel", back_populates="Beleidsmodules")


class Maatregel(Base):
    __tablename__ = "Maatregelen"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Maatregelen"
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    Created_By_UUID = Column(
        "Created_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )
    Modified_By_UUID = Column(
        "Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )

    Titel = Column(Unicode, nullable=False)
    Omschrijving = Column(Unicode)
    Toelichting = Column(Unicode)
    Toelichting_Raw = Column(Unicode)
    Weblink = Column(Unicode)
    Gebied_UUID = Column("Gebied", ForeignKey("Werkingsgebieden.UUID"))
    Status = Column(Unicode(50))
    Gebied_Duiding = Column(Unicode)
    Tags = Column(Unicode)

    Aanpassing_Op_UUID = Column("Aanpassing_Op", ForeignKey("Maatregelen.UUID"))
    Eigenaar_1_UUID = Column("Eigenaar_1", ForeignKey("Gebruikers.UUID"))
    Eigenaar_2_UUID = Column("Eigenaar_2", ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1_UUID = Column(
        "Portefeuillehouder_1", ForeignKey("Gebruikers.UUID")
    )
    Portefeuillehouder_2_UUID = Column(
        "Portefeuillehouder_2", ForeignKey("Gebruikers.UUID")
    )
    Opdrachtgever_UUID = Column("Opdrachtgever", ForeignKey("Gebruikers.UUID"))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Maatregel.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Maatregel.Modified_By_UUID == Gebruiker.UUID"
    )

    Beleidskeuzes = relationship("Beleidskeuze_Maatregelen", back_populates="Maatregel")
    Beleidsmodules = relationship(
        "Beleidsmodule_Maatregelen", back_populates="Maatregel"
    )

    Aanpassing_Op = relationship(
        "Maatregel", primaryjoin="Maatregel.Aanpassing_Op_UUID == Maatregel.UUID"
    )
    Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Eigenaar_1_UUID == Gebruiker.UUID"
    )
    Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Eigenaar_2_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_1 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Portefeuillehouder_1_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_2 = relationship(
        "Gebruiker", primaryjoin="Maatregel.Portefeuillehouder_2_UUID == Gebruiker.UUID"
    )
    Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Maatregel.Opdrachtgever_UUID == Gebruiker.UUID"
    )
    Gebied = relationship(
        "Werkingsgebied", primaryjoin="Maatregel.Gebied_UUID == Werkingsgebied.UUID"
    )
