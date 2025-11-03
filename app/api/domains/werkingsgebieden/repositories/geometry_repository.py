import uuid
from abc import ABCMeta, abstractmethod

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingTable


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

    def create_onderverdeling(
        self,
        session: Session,
        onderverdeling: InputGeoOnderverdelingTable,
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
                Input_GEO_Onderverdeling
            SET
                Geometry = {self._text_to_shape("geometry")}
            WHERE
                UUID = :uuid
            """
        session.execute(text(sql), params)
