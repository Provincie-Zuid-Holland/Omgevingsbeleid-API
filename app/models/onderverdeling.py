from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    text,
    DateTime,
    Unicode,
    Sequence,
)
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base
from app.util.sqlalchemy import Geometry


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

    Created_By_UUID = Column(
        "Created_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )
    Modified_By_UUID = Column(
        "Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )

    Onderverdeling = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265))
    Werkingsgebied_Description = Column("Werkingsgebied", Unicode(256))
    Werkingsgebied_UUID = Column(
        "UUID_Werkingsgebied", ForeignKey("Werkingsgebieden.UUID"), nullable=False
    )
    SHAPE = deferred(Column(Geometry, nullable=False))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Onderverdeling.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Onderverdeling.Modified_By_UUID == Gebruiker.UUID"
    )
    Werkingsgebied = relationship(
        "Werkingsgebied",
        primaryjoin="Onderverdeling.Werkingsgebied_UUID == Werkingsgebied.UUID",
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
            "Onderverdeling",
            "Werkingsgebied_Description",
            "Werkingsgebied_UUID"
        ]

