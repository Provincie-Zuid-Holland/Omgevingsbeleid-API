import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime

from sqlalchemy import text

from app.core.utils.utils import as_datetime
from app.dynamic.repository.repository import BaseRepository
from app.extensions.areas.db.tables import AreasTable


class AreaGeometryRepository(BaseRepository, metaclass=ABCMeta):
    @abstractmethod
    def _text_to_shape(self, key: str) -> str:
        pass

    @abstractmethod
    def _shape_to_text(self, column: str) -> str:
        pass

    @abstractmethod
    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        pass

    def create_area(
        self,
        uuidx: uuid.UUID,
        created_date: datetime,
        created_by_uuid: uuid.UUID,
        werkingsgebied: dict,
    ):
        area = AreasTable(
            UUID=uuidx,
            Created_Date=created_date,
            Created_By_UUID=created_by_uuid,
            Shape=None,
            Gml=werkingsgebied.get("GML"),
            Source_UUID=uuid.UUID(werkingsgebied.get("UUID")),
            Source_ID=werkingsgebied.get("ID"),
            Source_Title=werkingsgebied.get("Title"),
            Source_Symbol=werkingsgebied.get("Symbol"),
            Source_Start_Validity=as_datetime(werkingsgebied.get("Start_Validity")),
            Source_End_Validity=as_datetime(werkingsgebied.get("End_Validity")),
            Source_Created_Date=as_datetime(werkingsgebied.get("Created_Date")),
            Source_Modified_Date=as_datetime(werkingsgebied.get("Modified_Date")),
        )
        self._db.add(area)
        self._db.flush()

        params = {
            "uuid": self._format_uuid(uuidx),
            "shape": werkingsgebied.get("Geometry"),
        }
        sql = f"""
            UPDATE
                areas
            SET
                Shape = {self._text_to_shape("shape")}
            WHERE
                UUID = :uuid
            """
        self._db.execute(text(sql), params)
