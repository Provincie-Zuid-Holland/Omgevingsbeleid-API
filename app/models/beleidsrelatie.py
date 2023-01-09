from typing import List, TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, Unicode, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from app.db.base_class import Base


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidsrelatie(Base):
    __tablename__ = "Beleidsrelaties"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Beleidsrelaties"
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    # @todo: these 4 values have different nullable values then all other models
    # we should align them at some point
    Begin_Geldigheid = Column(DateTime, nullable=True)
    Eind_Geldigheid = Column(DateTime, nullable=True)
    Created_Date = Column(DateTime, nullable=True)
    Modified_Date = Column(DateTime, nullable=True)

    Created_By_UUID = Column(
        "Created_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )
    Modified_By_UUID = Column(
        "Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False
    )

    Omschrijving = Column(Unicode)
    Status = Column(Unicode(50))
    Aanvraag_Datum = Column(DateTime)
    Datum_Akkoord = Column(DateTime)
    Titel = Column(Unicode(50), nullable=False, server_default=text("('Titel')"))

    Van_Beleidskeuze_UUID = Column(
        "Van_Beleidskeuze", ForeignKey("Beleidskeuzes.UUID"), nullable=False
    )
    Naar_Beleidskeuze_UUID = Column(
        "Naar_Beleidskeuze", ForeignKey("Beleidskeuzes.UUID"), nullable=False
    )

    Created_By = relationship(
        "Gebruiker", primaryjoin="Beleidsrelatie.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Beleidsrelatie.Modified_By_UUID == Gebruiker.UUID"
    )

    Van_Beleidskeuze = relationship(
        "Beleidskeuze",
        primaryjoin="Beleidsrelatie.Van_Beleidskeuze_UUID == Beleidskeuze.UUID",
        lazy="joined",
    )
    Naar_Beleidskeuze = relationship(
        "Beleidskeuze",
        primaryjoin="Beleidsrelatie.Naar_Beleidskeuze_UUID == Beleidskeuze.UUID",
        lazy="joined",
    )

    @classmethod
    def get_allowed_filter_keys(cls) -> List[str]:
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
            "Omschrijving",
            "Status",
            "Aanvraag_Datum",
            "Datum_Akkoord",
            "Van_Beleidskeuze_UUID",
            "Naar_Beleidskeuze_UUID",
        ]
