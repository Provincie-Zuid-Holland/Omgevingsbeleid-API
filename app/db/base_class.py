from typing import Any

from sqlalchemy import Column, Integer, DateTime, text, ForeignKey, MetaData, Sequence
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.schema import Sequence


@as_declarative()
class Base:
    __name__: str


@as_declarative()
class ImmutableBase(Base):
    def ID(cls):
        seq_name = "seq_{name}".format(name=cls.__name__)
        seq = Sequence(seq_name)
        return Column(Integer, seq, nullable=False, server_default=seq.next_value())

    UUID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    @declared_attr
    def Created_By(cls):
        return Column("Created_By", ForeignKey("Gebruikers.UUID"), nullable=False)

    @declared_attr
    def Modified_By(cls):
        return Column("Modified_By", ForeignKey("Gebruikers.UUID"), nullable=False)
