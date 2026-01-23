from typing import Optional
import uuid
from abc import ABCMeta, abstractmethod

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


class WerkingsgebiedHash(BaseModel):
    UUID: uuid.UUID
    hash: str


class GeometryRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def _text_to_shape(self, key: str) -> str:
        pass

    @abstractmethod
    def _shape_to_text(self, column: str) -> str:
        pass

    @abstractmethod
    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        pass

    @abstractmethod
    def _calculate_hex(self, column: str) -> str:
        pass

    def create_onderverdeling(
        self,
        session: Session,
        onderverdeling: InputGeoOnderverdelingenTable,
        geometry: str,
    ):
        session.add(onderverdeling)
        session.flush()
        session.commit()

        params = {
            "uuid": self._format_uuid(onderverdeling.UUID),
            "geometry": geometry,
        }
        sql = f"""
            UPDATE
                "Input_GEO_Onderverdeling"
            SET
                "Geometry" = {self._text_to_shape("geometry")}
            WHERE
                "UUID" = :uuid
            """
        session.execute(text(sql), params)

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
