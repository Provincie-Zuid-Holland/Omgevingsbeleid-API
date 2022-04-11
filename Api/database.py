from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime, text, ForeignKey, MetaData, Sequence
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.schema import Sequence


class CommonMixin:
    @declared_attr
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


# Naming conventions for keys, used to map to the current database setup
metadata = MetaData(
    naming_convention={
        "pk": "PK_%(table_name)s",
        "fk": "FK_%(table_name)s_%(column_0_name)s",
        "ix": "IX_%(table_name)s_%(column_0_name)s",
        "uq": "UQ_%(table_name)s_%(column_0_name)s",
        "ck": "CK_%(table_name)s_%(constraint_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)
