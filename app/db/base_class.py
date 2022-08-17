from typing import Any, List

from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.ext.declarative import as_declarative

metadata = MetaData(
    naming_convention={
        "pk": "PK_%(table_name)s",
        "fk": "FK_%(table_name)s_%(column_0_name)s",
        "ix": "IX_%(table_name)s_%(column_0_name)s",
        "uq": "UQ_%(table_name)s_%(column_0_name)s",
        "ck": "CK_%(table_name)s_%(constraint_name)s",
    }
)

NULL_UUID = "00000000-0000-0000-0000-000000000000"


@as_declarative(metadata=metadata)
class Base:
    ID: Any
    __name__: str

    def get_allowed_filter_keys() -> List[str]:
        return []


@as_declarative(metadata=metadata)
class BaseTimeStamped:
    #TODO: we should only have 1 base, so this base should extend the `class Base`
    ID: Any

    Begin_Geldigheid = Column(DateTime, nullable=False)
    Eind_Geldigheid = Column(DateTime, nullable=False)
    Created_Date = Column(DateTime, nullable=False)
    Modified_Date = Column(DateTime, nullable=False)

    __name__: str
