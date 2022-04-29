from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, text, DateTime, Unicode, Sequence
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base

if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidsmodule(Base):
    __tablename__ = "Beleidsmodules"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Beleidsmodules"
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    Created_By = Column("Created_By", ForeignKey("Gebruikers.UUID"), nullable=False)
    Modified_By = Column("Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False)


    Titel = Column(Unicode(150), nullable=False)
    Besluit_Datum = Column(DateTime)

    # Created_By_Gebruiker = relationship(
    #     "Gebruiker", primaryjoin="Beleidsmodules.Created_By == Gebruikers.UUID"
    # )
    # Modified_By_Gebruiker = relationship(
    #     "Gebruiker", primaryjoin="Beleidsmodules.Modified_By == Gebruikers.UUID"
    # )

    Maatregelen = relationship("Beleidsmodule_Maatregelen", back_populates="Beleidsmodule")
    Beleidskeuzes = relationship("Beleidsmodule_Beleidskeuzes", back_populates="Beleidsmodule")
