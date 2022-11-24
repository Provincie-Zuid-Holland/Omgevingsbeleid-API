from typing import Any, List

from sqlalchemy import Column, MetaData
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.util import ImmutableProperties
from sqlalchemy_utils import get_mapper, get_columns

from app.core.exceptions import SearchException


NULL_UUID = "00000000-0000-0000-0000-000000000000"

metadata = MetaData(
    naming_convention={
        "pk": "PK_%(table_name)s",
        "fk": "FK_%(table_name)s_%(column_0_name)s",
        "ix": "IX_%(table_name)s_%(column_0_name)s",
        "uq": "UQ_%(table_name)s_%(column_0_name)s",
        "ck": "CK_%(table_name)s_%(constraint_name)s",
    }
)


@as_declarative(metadata=metadata)
class Base:
    ID: Any
    __name__: str

    @classmethod
    def get_columns(cls) -> List[Column]:
        return get_columns(cls)

    @classmethod
    def get_relationships(cls) -> ImmutableProperties:
        return get_mapper(cls).relationships

    @classmethod
    def get_base_column_keys(cls) -> List[str]:
        """
        Returns all columns names excluding foreign keys
        """
        all_cols: List[Column] = get_columns(cls)
        base_columns = list()
        for c in all_cols:
            if len(c.foreign_keys) == 0:
                base_columns.append(c.key)

        return base_columns

    @classmethod
    def get_foreign_column_keys(cls) -> List[str]:
        """
        Returns all columns registered as foreign keys
        """
        all_cols: List[Column] = get_columns(cls)
        foreign_keys = list()
        for c in all_cols:
            if len(c.foreign_keys) != 0:
                foreign_keys.append(c.key)

        return foreign_keys

    @classmethod
    def get_allowed_filter_keys(cls) -> List[str]:
        raise SearchException("Model not searchable")

    @classmethod
    def get_search_fields(cls):
        raise SearchException("Model not searchable")


# @as_declarative(metadata=metadata)
# class BaseTimeStamped:
#    # TODO: we should only have 1 base, so this base should extend the `class Base`
#    ID: Any
#
#    Begin_Geldigheid = Column(DateTime, nullable=False)
#    Eind_Geldigheid = Column(DateTime, nullable=False)
#    Created_Date = Column(DateTime, nullable=False)
#    Modified_Date = Column(DateTime, nullable=False)
#
#    __name__: str
