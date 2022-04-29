from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, DateTime, Unicode, Sequence
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base

if TYPE_CHECKING:
    from .gebruikers import Gebruikers  # noqa: F401
    from .beleidsmodule import Beleidsmodule  # noqa: F401


class Beleidsmodule_Beleidskeuzes(Base):
    __tablename__ = "Beleidsmodule_Beleidskeuzes"

    Beleidsmodule_UUID = Column(
        "Beleidsmodule_UUID", ForeignKey("Beleidsmodules.UUID"), primary_key=True
    )
    Beleidskeuze_UUID = Column(
        "Beleidskeuze_UUID", ForeignKey("Beleidskeuzes.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidsmodule = relationship("Beleidsmodule", back_populates="Beleidskeuzes")
    Beleidskeuze = relationship("Beleidskeuze", back_populates="Beleidsmodules")


class Beleidskeuze(Base):
    __tablename__ = "Beleidskeuzes"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Beleidskeuzes"
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


    Eigenaar_1 = Column(ForeignKey("Gebruikers.UUID"))
    Eigenaar_2 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1 = Column(ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_2 = Column(ForeignKey("Gebruikers.UUID"))
    Opdrachtgever = Column(ForeignKey("Gebruikers.UUID"))
    Titel = Column(Unicode, nullable=False)
    Omschrijving_Keuze = Column(Unicode)
    Omschrijving_Werking = Column(Unicode)
    Provinciaal_Belang = Column(Unicode)
    Aanleiding = Column(Unicode)
    Afweging = Column(Unicode)
    Besluitnummer = Column(Unicode)
    Tags = Column(Unicode)
    Aanpassing_Op = Column(ForeignKey("Beleidskeuzes.UUID"))
    Status = Column(Unicode(50), nullable=False)
    Weblink = Column(Unicode(200))

    Created_By_Gebruiker = relationship(
        "Gebruiker", primaryjoin="Beleidskeuzes.Created_By == Gebruikers.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruiker", primaryjoin="Beleidskeuzes.Modified_By == Gebruikers.UUID"
    )

    Ref_Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Beleidskeuzes.Eigenaar_1 == Gebruikers.UUID"
    )
    Ref_Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Beleidskeuzes.Eigenaar_2 == Gebruikers.UUID"
    )
    Ref_Portefeuillehouder_1 = relationship(
        "Gebruiker",
        primaryjoin="Beleidskeuzes.Portefeuillehouder_1 == Gebruikers.UUID",
    )
    Ref_Portefeuillehouder_2 = relationship(
        "Gebruiker",
        primaryjoin="Beleidskeuzes.Portefeuillehouder_2 == Gebruikers.UUID",
    )
    Ref_Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Beleidskeuzes.Opdrachtgever == Gebruikers.UUID"
    )
    Ambities = relationship("Beleidskeuze_Ambities", back_populates="Beleidskeuze")
    Belangen = relationship("Beleidskeuze_Belangen", back_populates="Beleidskeuze")
    Beleidsdoelen = relationship(
        "Beleidskeuze_Beleidsdoelen", back_populates="Beleidskeuze"
    )
    Beleidsprestaties = relationship(
        "Beleidskeuze_Beleidsprestaties", back_populates="Beleidskeuze"
    )
    Beleidsregels = relationship(
        "Beleidskeuze_Beleidsregels", back_populates="Beleidskeuze"
    )
    Maatregelen = relationship(
        "Beleidskeuze_Maatregelen", back_populates="Beleidskeuze"
    )
    Themas = relationship("Beleidskeuze_Themas", back_populates="Beleidskeuze")
    Verordeningen = relationship(
        "Beleidskeuze_Verordeningen", back_populates="Beleidskeuze"
    )
    Werkingsgebieden = relationship(
        "Beleidskeuze_Werkingsgebieden", back_populates="Beleidskeuze"
    )
    # Beleidsrelaties = relationship("Beleidsrelaties", back_populates="Beleidskeuzes")
    Beleidsmodules = relationship(
        "Beleidsmodule_Beleidskeuzes", back_populates="Beleidskeuze"
    )

