from typing import Any

from sqlalchemy import Column, Integer, DateTime, text, ForeignKey, MetaData, Sequence
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.schema import Sequence


@as_declarative()
class Base:
    __name__: str
