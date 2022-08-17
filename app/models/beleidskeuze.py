from typing import List, TYPE_CHECKING, List

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidsmodule import Beleidsmodule  # noqa: F401


class Beleidsmodule_Beleidskeuzes(Base):
    __tablename__ = "Beleidsmodule_Beleidskeuzes"

    Beleidsmodule_UUID = Column(ForeignKey("Beleidsmodules.UUID"), primary_key=True)
    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

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
    Created_By_UUID = Column(
        "Created_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )
    Modified_By_UUID = Column(
        "Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )

    Eigenaar_1_UUID = Column("Eigenaar_1", ForeignKey("Gebruikers.UUID"))
    Eigenaar_2_UUID = Column("Eigenaar_2", ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1_UUID = Column(
        "Portefeuillehouder_1", ForeignKey("Gebruikers.UUID")
    )
    Portefeuillehouder_2_UUID = Column(
        "Portefeuillehouder_2", ForeignKey("Gebruikers.UUID")
    )
    Opdrachtgever_UUID = Column("Opdrachtgever", ForeignKey("Gebruikers.UUID"))
    Aanpassing_Op_UUID = Column("Aanpassing_Op", ForeignKey("Beleidskeuzes.UUID"))

    Titel = Column(Unicode, nullable=False)
    Omschrijving_Keuze = Column(Unicode)
    Omschrijving_Werking = Column(Unicode)
    Provinciaal_Belang = Column(Unicode)
    Aanleiding = Column(Unicode)
    Afweging = Column(Unicode)
    Besluitnummer = Column(Unicode)
    Tags = Column(Unicode)
    Status = Column(Unicode(50), nullable=False)
    Weblink = Column(Unicode(200))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Beleidskeuze.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Beleidskeuze.Modified_By_UUID == Gebruiker.UUID"
    )

    Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Beleidskeuze.Eigenaar_1_UUID == Gebruiker.UUID"
    )
    Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Beleidskeuze.Eigenaar_2_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_1 = relationship(
        "Gebruiker",
        primaryjoin="Beleidskeuze.Portefeuillehouder_1_UUID == Gebruiker.UUID",
    )
    Portefeuillehouder_2 = relationship(
        "Gebruiker",
        primaryjoin="Beleidskeuze.Portefeuillehouder_2_UUID == Gebruiker.UUID",
    )
    Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Beleidskeuze.Opdrachtgever_UUID == Gebruiker.UUID"
    )
    Aanpassing_Op = relationship(
        "Beleidskeuze",
        primaryjoin="Beleidskeuze.Aanpassing_Op_UUID == Beleidskeuze.UUID",
    )

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
    Beleidsmodules = relationship(
        "Beleidsmodule_Beleidskeuzes", back_populates="Beleidskeuze"
    )

    Van_Beleidsrelaties = relationship(
        "Beleidsrelatie",
        primaryjoin="Beleidskeuze.UUID == Beleidsrelatie.Van_Beleidskeuze_UUID",
    )
    Naar_Beleidsrelaties = relationship(
        "Beleidsrelatie",
        primaryjoin="Beleidskeuze.UUID == Beleidsrelatie.Naar_Beleidskeuze_UUID",
    )

    def get_allowed_filter_keys() -> List[str]:
        return [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_Date",
            "Modified_Date",
            "Created_By_UUID",
            "Modified_By_UUID",
            "Titel",
            "Omschrijving_Keuze",
            "Omschrijving_Werking",
            "Provinciaal_Belang",
            "Aanleiding",
            "Afweging",
            "Besluitnummer",
            "Weblink",
            "Status",
            "Tags",
        ]
