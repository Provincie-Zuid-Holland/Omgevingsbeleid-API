from typing import Optional
from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class HasUUID:
    UUID: Mapped[uuid.UUID] = mapped_column(
        primary_key=True
    )


class TimeStamped:
    Created_Date: Mapped[Optional[datetime]]
    Modified_Date: Mapped[Optional[datetime]]


class UserMetaData:
    Created_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))
    Modified_By_UUID: Mapped[uuid.UUID] = mapped_column(ForeignKey("Gebruikers.UUID"))


class HasIDType:
    Object_Type: Mapped[str] = mapped_column(String(25))
    Object_ID: Mapped[int]
