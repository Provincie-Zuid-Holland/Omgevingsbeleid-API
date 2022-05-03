from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, DateTime, Unicode, Sequence
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base

if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401


class Onderverdeling(Base):
    __tablename__ = "Onderverdeling"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Onderverdeling"
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    Created_By_UUID = Column('Created_By', UNIQUEIDENTIFIER, ForeignKey("Gebruikers.UUID"), nullable=False)
    Modified_By_UUID = Column('Modified_By', UNIQUEIDENTIFIER, ForeignKey("Gebruikers.UUID"), nullable=False)

    Onderverdeling = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265))  # @todo: length feels like a typo
    Werkingsgebied_Description = Column('Werkingsgebied', Unicode(256))
    Werkingsgebied_UUID = Column('UUID_Werkingsgebied', ForeignKey("Werkingsgebieden.UUID"), nullable=False)
    SHAPE = deferred(Column(Geometry, nullable=False))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Onderverdeling.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Onderverdeling.Modified_By_UUID == Gebruiker.UUID"
    )
    Werkingsgebied = relationship(
        "Werkingsgebied", primaryjoin="Onderverdeling.Werkingsgebied_UUID == Werkingsgebied.UUID"
    )
