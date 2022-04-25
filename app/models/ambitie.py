from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base, ImmutableBase

if TYPE_CHECKING:
    from .gebruikers import Gebruikers  # noqa: F401


class Beleidskeuze_Ambities(Base):
    __tablename__ = "Beleidskeuze_Ambities"

    Beleidskeuze_UUID = Column(
        "Beleidskeuze_UUID", ForeignKey("Beleidskeuze.UUID"), primary_key=True
    )
    Ambitie_UUID = Column("Ambitie_UUID", ForeignKey("Ambitie.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Ambities")
    Ambitie = relationship("Ambitie", back_populates="Beleidskeuzes")


class Ambitie(ImmutableBase):
    __tablename__ = "Ambities"

    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)

    Created_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Ambitie.Created_By == Gebruiker.UUID"
    )
    Modified_By_Gebruiker = relationship(
        "Gebruikers", primaryjoin="Ambitie.Modified_By == Gebruiker.UUID"
    )
    Beleidskeuzes = relationship("Beleidskeuze_Ambities", back_populates="Ambitie")
