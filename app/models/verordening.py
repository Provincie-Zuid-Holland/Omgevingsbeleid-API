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
from app.util.legacy_helpers import SearchFields


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidskeuze_Verordeningen(Base):
    __tablename__ = "Beleidskeuze_Verordeningen"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Verordening_UUID = Column(ForeignKey("Verordeningen.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Verordeningen")
    Verordening = relationship("Verordening", back_populates="Beleidskeuzes")


class Verordening(Base):
    __tablename__ = "Verordeningen"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Verordeningen"
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

    Portefeuillehouder_1_UUID = Column(
        "Portefeuillehouder_1", ForeignKey("Gebruikers.UUID")
    )
    Portefeuillehouder_2_UUID = Column(
        "Portefeuillehouder_2", ForeignKey("Gebruikers.UUID")
    )
    Eigenaar_1_UUID = Column("Eigenaar_1", ForeignKey("Gebruikers.UUID"))
    Eigenaar_2_UUID = Column("Eigenaar_2", ForeignKey("Gebruikers.UUID"))
    Opdrachtgever_UUID = Column("Opdrachtgever", ForeignKey("Gebruikers.UUID"))

    Titel = Column(Unicode)
    Inhoud = Column(Unicode)
    Weblink = Column(Unicode)
    Status = Column(Unicode(50), nullable=False)
    Type = Column(Unicode, nullable=False)
    Gebied_UUID = Column("Gebied", ForeignKey("Werkingsgebieden.UUID"))
    Volgnummer = Column(Unicode, nullable=False)

    Created_By = relationship(
        "Gebruiker", primaryjoin="Verordening.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Verordening.Modified_By_UUID == Gebruiker.UUID"
    )

    Portefeuillehouder_1 = relationship(
        "Gebruiker",
        primaryjoin="Verordening.Portefeuillehouder_1_UUID == Gebruiker.UUID",
    )
    Portefeuillehouder_2 = relationship(
        "Gebruiker",
        primaryjoin="Verordening.Portefeuillehouder_2_UUID == Gebruiker.UUID",
    )
    Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Verordening.Eigenaar_1_UUID == Gebruiker.UUID"
    )
    Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Verordening.Eigenaar_2_UUID == Gebruiker.UUID"
    )
    Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Verordening.Opdrachtgever_UUID == Gebruiker.UUID"
    )
    Gebied = relationship(
        "Werkingsgebied", primaryjoin="Verordening.Gebied_UUID == Werkingsgebied.UUID"
    )

    Beleidskeuzes = relationship(
        "Beleidskeuze_Verordeningen", back_populates="Verordening"
    )

    @classmethod
    def get_search_fields(cls):
        return SearchFields(title=cls.Titel, description=[cls.Inhoud])

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
            "Inhoud",
            "Weblink",
            "Gebied_UUID",
            "Status",
            "Type",
            "Volgnummer",
        ]
