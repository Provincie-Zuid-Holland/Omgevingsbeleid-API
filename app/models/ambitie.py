from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, DateTime, Unicode
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base

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


class Ambitie(Base):
    __tablename__ = "Ambities"

    def ID(cls):
        seq_name = "seq_{name}".format(name=cls.__name__)
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
