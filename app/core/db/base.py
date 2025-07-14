from sqlalchemy.orm import DeclarativeBase

from .metadata import table_metadata


class Base(DeclarativeBase):
    metadata = table_metadata
