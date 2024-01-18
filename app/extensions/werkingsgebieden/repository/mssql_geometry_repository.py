import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text

from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository


class MssqlGeometryRepository(GeometryRepository):
    def add_onderverdeling(
        self,
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
        if end_validity is None:
            end_validity = datetime(2070, 1, 1)

        params = {
            "uuid": str(uuidx),
            "id": idx,
            "title": title,
            "shape": text_shape,
            "symbol": symbol,
            "werkingsgebied": werkingsgebied_title,
            "uuid_werkingsgebied": str(werkingsgebied_uuid),
            "created_date": str(created_date),
            "modified_date": str(modified_date),
            "start_validity": str(start_validity),
            "end_validity": str(end_validity),
        }
        sql = f"""
            INSERT INTO
                Onderverdeling
                    (
                        UUID, ID, Onderverdeling, SHAPE, symbol, Werkingsgebied, UUID_Werkingsgebied,
                        Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid
                    )
                VALUES
                    (
                        :uuid, :id, :title, geometry::STGeomFromText(:shape, 28992), :symbol, :werkingsgebied, :uuid_werkingsgebied,
                        :created_date, :modified_date, :start_validity, :end_validity
                    )
            """
        self._db.execute(text(sql), params)

    def add_werkingsgebied(
        self,
        uuidx: uuid.UUID,
        idx: int,
        title: str,
        text_shape: str,
        created_date: datetime,
        modified_date: datetime,
        start_validity: datetime,
        end_validity: Optional[datetime],
    ):
        if end_validity is None:
            end_validity = datetime(2070, 1, 1)

        params = {
            "uuid": str(uuidx),
            "id": idx,
            "title": title,
            "shape": text_shape,
            "created_date": str(created_date),
            "modified_date": str(modified_date),
            "start_validity": str(start_validity),
            "end_validity": str(end_validity),
        }
        sql = f"""
            INSERT INTO
                Werkingsgebieden
                    (
                        UUID, ID, Werkingsgebied, SHAPE,
                        Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid
                    )
                VALUES
                    (
                        :uuid, :id, :title, geometry::STGeomFromText(:shape, 28992),
                        :created_date, :modified_date, :start_validity, :end_validity
                    )
            """
        self._db.execute(text(sql), params)
