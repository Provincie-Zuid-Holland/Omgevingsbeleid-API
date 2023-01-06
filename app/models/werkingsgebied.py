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
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, deferred
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base
from app.util.sqlalchemy import Geometry


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidskeuze_Werkingsgebieden(Base):
    __tablename__ = "Beleidskeuze_Werkingsgebieden"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Werkingsgebied_UUID = Column(ForeignKey("Werkingsgebieden.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Werkingsgebieden")
    Werkingsgebied = relationship("Werkingsgebied", back_populates="Beleidskeuzes")


class Werkingsgebied(Base):
    __tablename__ = "Werkingsgebieden"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Werkingsgebieden"
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

    Werkingsgebied = Column(Unicode, nullable=False)
    symbol = Column(Unicode(265))
    SHAPE = deferred(Column(Geometry(), nullable=False))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Werkingsgebied.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Werkingsgebied.Modified_By_UUID == Gebruiker.UUID"
    )

    Beleidskeuzes = relationship(
        Beleidskeuze_Werkingsgebieden, back_populates="Werkingsgebied", lazy="dynamic"
    )

    @hybrid_property
    def All_Beleidskeuzes(self):
        return self.Beleidskeuzes.all()

    @hybrid_property
    def Valid_Beleidskeuzes(self):
        from app.crud.crud_beleidskeuze import CRUDBeleidskeuze

        valid_beleidskeuzes = CRUDBeleidskeuze.valid_view_static()
        return self.Beleidskeuzes.join(
            valid_beleidskeuzes,
            valid_beleidskeuzes.UUID == Beleidskeuze_Werkingsgebieden.Beleidskeuze_UUID,
        ).all()

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
            "Werkingsgebied",
        ]
