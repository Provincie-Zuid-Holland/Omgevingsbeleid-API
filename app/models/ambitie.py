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


class Beleidsdoel_Ambities(Base):
    __tablename__ = "Beleidsdoel_Ambities"

    Beleidsdoel_UUID = Column(ForeignKey("Beleidsdoelen.UUID"), primary_key=True)
    Ambitie_UUID = Column(ForeignKey("Ambities.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidsdoel = relationship("Beleidsdoel", back_populates="Ambities")
    Ambitie = relationship("Ambitie", back_populates="Beleidsdoelen")


class Ambitie(Base):
    __tablename__ = "Ambities"

    @declared_attr
    def ID(cls):
        seq_name = "seq_Ambities"
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

    Created_By = relationship(
        "Gebruiker", primaryjoin="Ambitie.Created_By_UUID == Gebruiker.UUID"
    )
    Modified_By = relationship(
        "Gebruiker", primaryjoin="Ambitie.Modified_By_UUID == Gebruiker.UUID"
    )

    Beleidsdoelen = relationship(
        "Beleidsdoel_Ambities", back_populates="Ambitie", lazy="dynamic"
    )

    @hybrid_property
    def All_Beleidsdoelen(self):
        return self.Beleidskeuzes.all()

    @hybrid_property
    def Valid_Beleidsdoelen(self):
        from app.crud.crud_beleidsdoel import crud_beleidsdoel
        valid_beleidsdoelen = crud_beleidsdoel.valid_view_as_subquery()
        return self.Beleidsdoelen.join(
            valid_beleidsdoelen,
            valid_beleidsdoelen.UUID == Beleidsdoel_Ambities.Beleidsdoel_UUID,
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
            "Titel",
            "Omschrijving",
            "Weblink",
            "Created_By_UUID",
            "Modified_By_UUID",
        ]
