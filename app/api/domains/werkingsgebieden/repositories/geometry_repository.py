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
    def _format_uuid(self, idx: uuid.UUID) -> str:
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
            "id": self._format_uuid(onderverdeling.id),
            "geometry": geometry,
        }
        sql = f"""
            UPDATE
                input_geo_onderverdeling
            SET
                geometry = {self._text_to_shape("geometry")}
            WHERE
                id = :id
            """
        session.execute(text(sql), params)
