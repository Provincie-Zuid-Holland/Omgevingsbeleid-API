import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column


class TimeStamped:
    created_date: Mapped[datetime | None]
    modified_date: Mapped[datetime | None]


class RequireTimeStamped:
    created_date: Mapped[datetime]
    modified_date: Mapped[datetime]


class UserMetaData:
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
    modified_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


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

    def to_dict_clean(self):
        return {
            c.key: self.serialize(getattr(self, c.key))
            for c in inspect(self).mapper.column_attrs
            if getattr(self, c.key) is not None
        }
