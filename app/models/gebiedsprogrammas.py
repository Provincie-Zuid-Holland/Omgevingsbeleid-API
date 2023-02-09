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
from sqlalchemy_utils.functions.orm import hybrid_property

from app.db.base_class import Base
from app.db.base_class import SearchFields


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Maatregel_Gebiedsprogrammas(Base):
    __tablename__ = "Maatregel_Gebiedsprogrammas"

    Maatregel_UUID = Column(ForeignKey("Maatregelen.UUID"), primary_key=True)
    Gebiedsprogramma_UUID = Column(
        ForeignKey("Gebiedsprogrammas.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Maatregel = relationship("Maatregel", back_populates="Gebiedsprogrammas")
    Gebiedsprogramma = relationship("Gebiedsprogramma", back_populates="Maatregelen")


class Beleidsmodule_Gebiedsprogrammas(Base):
    __tablename__ = "Beleidsmodule_Gebiedsprogrammas"

    Beleidsmodule_UUID = Column(
        "Beleidsmodule_UUID", ForeignKey("Beleidsmodules.UUID"), primary_key=True
    )
    Gebiedsprogramma_UUID = Column(
        "Gebiedsprogramma_UUID", ForeignKey("Gebiedsprogrammas.UUID"), primary_key=True
    )
    Koppeling_Omschrijving = Column(
        "Koppeling_Omschrijving", String(collation="SQL_Latin1_General_CP1_CI_AS")
    )

    Beleidsmodule = relationship("Beleidsmodule", back_populates="Gebiedsprogrammas")
    Gebiedsprogramma = relationship("Gebiedsprogramma", back_populates="Beleidsmodules")


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

    Eigenaar_1_UUID = Column("Eigenaar_1", ForeignKey("Gebruikers.UUID"))
    Eigenaar_2_UUID = Column("Eigenaar_2", ForeignKey("Gebruikers.UUID"))
    Portefeuillehouder_1_UUID = Column(
        "Portefeuillehouder_1", ForeignKey("Gebruikers.UUID")
    )
    Portefeuillehouder_2_UUID = Column(
        "Portefeuillehouder_2", ForeignKey("Gebruikers.UUID")
    )
    Opdrachtgever_UUID = Column("Opdrachtgever", ForeignKey("Gebruikers.UUID"))

    Status = Column(Unicode)
    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)
    Besluitnummer = Column(Unicode)
    Afbeelding = Column(Unicode)

    Created_By = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Modified_By_UUID == Gebruiker.UUID"
    )

    Eigenaar_1 = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Eigenaar_1_UUID == Gebruiker.UUID"
    )
    Eigenaar_2 = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Eigenaar_2_UUID == Gebruiker.UUID"
    )
    Portefeuillehouder_1 = relationship(
        "Gebruiker",
        primaryjoin="Gebiedsprogramma.Portefeuillehouder_1_UUID == Gebruiker.UUID",
    )
    Portefeuillehouder_2 = relationship(
        "Gebruiker",
        primaryjoin="Gebiedsprogramma.Portefeuillehouder_2_UUID == Gebruiker.UUID",
    )
    Opdrachtgever = relationship(
        "Gebruiker", primaryjoin="Gebiedsprogramma.Opdrachtgever_UUID == Gebruiker.UUID"
    )

    Maatregelen = relationship(
        "Maatregel_Gebiedsprogrammas", back_populates="Gebiedsprogramma", lazy="dynamic"
    )

    Beleidsmodules = relationship(
        "Beleidsmodule_Gebiedsprogrammas",
        back_populates="Gebiedsprogramma",
        # lazy="dynamic"
    )

    @hybrid_property
    def All_Maatregelen(self):
        return self.Maatregelen.all()  # TODO: check valid/nonvalid

    @hybrid_property
    def Valid_Maatregelen(self):
        from app.crud.crud_maatregel import CRUDMaatregel

        valid = CRUDMaatregel.valid_view_static()
        return self.Maatregelen.join(
            valid,
            valid.UUID == Maatregel_Gebiedsprogrammas.Maatregel_UUID,
        ).all()

    @classmethod
    def get_search_fields(cls):
        return SearchFields(title=cls.Titel, description=[cls.Omschrijving])

    @classmethod
    def get_allowed_filter_keys(cls) -> List[str]:
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
            "Besluitnummer",
            "Created_By_UUID",
            "Modified_By_UUID",
            "Eigenaar_1_UUID",
            "Eigenaar_2_UUID",
            "Portefeuillehouder_1_UUID",
            "Portefeuillehouder_2_UUID",
        ]
