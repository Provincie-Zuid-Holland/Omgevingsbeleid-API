import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, Unicode
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class ChangeLogBaseColumns:
    ID: Mapped[int] = mapped_column(primary_key=True)

    Object_Type: Mapped[Optional[str]] = mapped_column(Unicode(25))
    Object_ID: Mapped[Optional[int]]

    Created_Date: Mapped[datetime]
    Created_By_UUID: Mapped[uuid.UUID]  # Explicit NO foreign key here, this is just a log

    Action_Type: Mapped[str] = mapped_column(Unicode)
    Action_Data: Mapped[Optional[str]] = mapped_column(Unicode)
    Before: Mapped[Optional[str]] = mapped_column(Unicode)
    After: Mapped[Optional[str]] = mapped_column(Unicode)


class ChangeLogTable(Base, ChangeLogBaseColumns):
    __tablename__ = "change_log"

    change_log_object_type_id = Index("change_log_action_type_id", "Action_Type", "Object_Type", "Object_ID")

    def __repr__(self) -> str:
        return f"ChangeLog(ID={self.ID!r})"
