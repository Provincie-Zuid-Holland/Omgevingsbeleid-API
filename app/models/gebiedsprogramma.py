from typing import TYPE_CHECKING, List

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
    from .maatregel import Maatregel  # noqa: F401


status_options = [
    "Definitief ontwerp GS",
    "Definitief ontwerp GS concept",
    "Ontwerp GS",
    "Ontwerp GS Concept",
    "Ontwerp in inspraak",
    "Ontwerp PS",
    "Vastgesteld",
    "Vigerend",
]


class Maatregel_Gebiedsprogrammas(Base):
    __tablename__ = "Maatregel_Gebiedsprogrammas"

    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Gebiedsprogramma_UUID = Column(
        ForeignKey("Gebiedsprogrammas.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Maatregel = relationship("Maatregel", back_populates="Gebiedsprogrammas")
    Gebiedsprogramma = relationship("Gebiedsprogramma", back_populates="Maatregelen")


class Gebiedsprogramma(Base):
    __tablename__ = "Gebiedsprogrammas"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Gebiedsprogrammas"
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

    Status = Column(Unicode(50), nullable=False)
    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Afbeelding = Column(Unicode)

    Created_By = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Modified_By_UUID == Gebruiker.UUID"
    )

    Maatregelen = relationship(
        "Maatregel_Gebiedsprogrammas", back_populates="Gebiedsprogramma"
    )

    def get_allowed_filter_keys() -> List[str]:
        return [
            "ID",
            "UUID",
            "Begin_Geldigheid",
            "Eind_Geldigheid",
            "Created_Date",
            "Modified_Date",
            "Status",
            "Titel",
            "Omschrijving",
            "Created_By_UUID",
            "Modified_By_UUID",
        ]
