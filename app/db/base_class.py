from typing import Any

from sqlalchemy import Column, Integer, DateTime, text, ForeignKey, MetaData, Sequence
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.schema import Sequence

metadata = MetaData(
    naming_convention = {
        "pk": "PK_%(table_name)s",
        "fk": "FK_%(table_name)s_%(column_0_name)s",
        "ix": "IX_%(table_name)s_%(column_0_name)s",
        "uq": "UQ_%(table_name)s_%(column_0_name)s",
        "ck": "CK_%(table_name)s_%(constraint_name)s",
    }
)

NULL_UUID = '00000000-0000-0000-0000-000000000000' 

@as_declarative(metadata=metadata)
class Base:
    ID: Any
    __name__: str
