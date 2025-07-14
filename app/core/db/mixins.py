import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column


class TimeStamped:
    Created_Date: Mapped[Optional[datetime]]
    Modified_Date: Mapped[Optional[datetime]]


class UserMetaData:
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
    Modified_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class HasIDType:
    Object_Type: Mapped[str] = mapped_column(Unicode(25))
    Object_ID: Mapped[int]


class SerializerMixin:
    @staticmethod
    def serialize(value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def to_dict(self):
        return {c.key: self.serialize(getattr(self, c.key)) for c in inspect(self).mapper.column_attrs}
