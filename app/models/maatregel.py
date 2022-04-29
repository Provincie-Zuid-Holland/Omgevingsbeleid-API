from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, DateTime, Unicode, Sequence
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

    Beleidskeuze_UUID = Column(
        "Beleidskeuze_UUID", ForeignKey("Beleidskeuzes.UUID"), primary_key=True
    )
    Maatregel_UUID = Column(
        "Maatregel_UUID", ForeignKey("Maatregelen.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Maatregelen")
    Maatregel = relationship("Maatregel", back_populates="Beleidskeuzes")


class Beleidsmodule_Maatregelen(Base):
    __tablename__ = "Beleidsmodule_Maatregelen"

    Beleidsmodule_UUID = Column(
        "Beleidsmodule_UUID", ForeignKey("Beleidsmodules.UUID"), primary_key=True
    )
    Maatregel_UUID = Column(
        "Maatregel_UUID", ForeignKey("Maatregelen.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidsmodule = relationship("Beleidsmodules", back_populates="Maatregelen")
    Maatregel = relationship("Maatregelen", back_populates="Beleidsmodules")


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

    @declared_attr
    def Created_By(cls):
        return Column("Created_By", ForeignKey("Gebruikers.UUID"), nullable=False)

    @declared_attr
    def Modified_By(cls):
        return Column("Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False)


    Titel = Column(Unicode, nullable=False)
    Omschrijving = Column(Unicode)
    Toelichting = Column(Unicode)
    Toelichting_Raw = Column(Unicode)
    Weblink = Column(Unicode)
    # Gebied = Column(ForeignKey("Werkingsgebieden.UUID"))
    Status = Column(Unicode(50))
    Gebied_Duiding = Column(Unicode)
    Tags = Column(Unicode)
    Aanpassing_Op = Column(ForeignKey("Maatregelen.UUID"))
    Eigenaar_1 = Column(ForeignKey("Gebruikers.UUID"))
    Eigenaar_2 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_2 = Column(ForeignKey("Gebruikers.UUID"))
    Opdrachtgever = Column(ForeignKey("Gebruikers.UUID"))

    Created_By_Gebruiker = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Modified_By == Gebruikers.UUID"
    )

    Beleidskeuzes = relationship("Beleidskeuze_Maatregelen", back_populates="Maatregel")

    Ref_Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Eigenaar_1 == Gebruikers.UUID"
    )
    Ref_Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Eigenaar_2 == Gebruikers.UUID"
    )
    Ref_Portefeuillehouder_1 = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Portefeuillehouder_1 == Gebruikers.UUID"
    )
    Ref_Portefeuillehouder_2 = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Portefeuillehouder_2 == Gebruikers.UUID"
    )
    Ref_Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Maatregelen.Opdrachtgever == Gebruikers.UUID"
    )
    # Ref_Gebied = relationship(
    #     "Werkingsgebieden", primaryjoin="Maatregelen.Gebied == Werkingsgebieden.UUID"
    # )
    Beleidsmodules = relationship(
        "Beleidsmodule_Maatregelen", back_populates="Maatregel"
    )
