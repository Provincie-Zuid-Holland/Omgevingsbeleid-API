from typing import List, TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Unicode,
    text,
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.util.legacy_helpers import SearchFields

if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidskeuze_Beleidsregels(Base):
    __tablename__ = "Beleidskeuze_Beleidsregels"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Beleidsregel_UUID = Column(ForeignKey("Beleidsregels.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Beleidsregels")
    Beleidsregel = relationship("Beleidsregel", back_populates="Beleidskeuzes")


class Beleidsregel(Base):
    __tablename__ = "Beleidsregels"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Beleidsregels"
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

    Titel = Column(Unicode(150), nullable=False)
    Omschrijving = Column(Unicode)
    Weblink = Column(Unicode)
    Externe_URL = Column(String(300, "SQL_Latin1_General_CP1_CI_AS"))

    Created_By = relationship(
        "Gebruiker", primaryjoin="Beleidsregel.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Beleidsregel.Modified_By_UUID == Gebruiker.UUID"
    )

    Beleidskeuzes = relationship(
        Beleidskeuze_Beleidsregels, back_populates="Beleidsregel", lazy="dynamic"
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
            valid_beleidskeuzes.UUID == Beleidskeuze_Beleidsregels.Beleidskeuze_UUID,
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
            "Created_By_UUID",
            "Modified_By_UUID",
            "Titel",
            "Omschrijving",
            "Weblink",
            "Externe_URL",
        ]
