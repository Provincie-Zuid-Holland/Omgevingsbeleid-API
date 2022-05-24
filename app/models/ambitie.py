from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    text,
    DateTime,
    Unicode,
    Sequence,
    Table,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import create_view

from app.db.base_class import Base


if TYPE_CHECKING:
    from .gebruiker import Gebruiker  # noqa: F401
    from .beleidskeuze import Beleidskeuze  # noqa: F401


class Beleidskeuze_Ambities(Base):
    __tablename__ = "Beleidskeuze_Ambities"

    Beleidskeuze_UUID = Column(ForeignKey("Beleidskeuzes.UUID"), primary_key=True)
    Ambitie_UUID = Column(ForeignKey("Ambities.UUID"), primary_key=True)
    Koppeling_Omschrijving = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))

    Beleidskeuze = relationship("Beleidskeuze", back_populates="Ambities")
    Ambitie = relationship("Ambitie", back_populates="Beleidskeuzes")


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
    Beleidskeuzes = relationship("Beleidskeuze_Ambities", back_populates="Ambitie")

    # SQL partitions through hybrid property expressions

    # @hybrid_property
    # def row_number(self):
    #     return -1

    # @row_number.expression
    # def row_number(cls):
    #     return sa.func.row_number().over(partition_by=cls.ID, order_by=cls.Modified_Date)


valid_ambitie_stmt = sa.select([Ambitie.UUID]).where(Ambitie.Weblink != "")
valid_ambitie_view = create_view("Valid_Ambities", valid_ambitie_stmt, Base.metadata)


class ViewValidAmbitie(Base):
    __table__ = valid_ambitie_view
