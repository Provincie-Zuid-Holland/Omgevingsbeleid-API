import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository


class WerkingsgebiedHash(BaseModel):
    UUID: uuid.UUID
    hash: str


class GeometryRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def add_onderverdeling(
        self,
        session: Session,
        uuidx: uuid.UUID,
        idx: int,
        title: str,
        text_shape: str,
        symbol: str,
        werkingsgebied_title: str,
        werkingsgebied_uuid: uuid.UUID,
        created_date: datetime,
        modified_date: datetime,
        start_validity: datetime,
        end_validity: Optional[datetime],
    ):
        pass

    @abstractmethod
    def add_werkingsgebied(
        self,
        session: Session,
        uuidx: uuid.UUID,
        idx: int,
        title: str,
        text_shape: str,
        gml: str,
        symbol: str,
        created_date: datetime,
        modified_date: datetime,
        start_validity: datetime,
        end_validity: Optional[datetime],
    ):
        pass

    @abstractmethod
    def get_werkingsgebied(self, session: Session, uuidx: uuid.UUID) -> dict:
        pass

    @abstractmethod
    def get_werkingsgebied_optional(self, session: Session, uuidx: uuid.UUID) -> Optional[dict]:
        pass

    @abstractmethod
    def get_onderverdelingen_for_werkingsgebied(self, session: Session, werkingsgebied_uuid: uuid.UUID) -> List[dict]:
        pass

    @abstractmethod
    def _calculate_hex(self, column: str) -> str:
        pass

    def get_latest_shape_hash_by_title(self, session: Session, title: str) -> Optional[WerkingsgebiedHash]:
        params = {
            "title": title,
        }
        sql = f"""
            SELECT
                UUID AS uuid,
                {self._calculate_hex("Shape")} AS shape_hash
            FROM
                Werkingsgebieden
            WHERE
                Werkingsgebied = :title
            ORDER BY
                Created_Date DESC
            """

        row = session.execute(text(sql), params).fetchone()
        if row is None:
            return None

        row_dict = row._asdict()
        werkingsgebied_hash = WerkingsgebiedHash(
            UUID=uuid.UUID(row_dict["uuid"]),
            hash=row_dict["shape_hash"],
        )

        return werkingsgebied_hash
