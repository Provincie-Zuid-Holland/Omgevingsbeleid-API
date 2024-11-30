import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.core.utils.utils import DATE_FORMAT
from app.dynamic.utils.pagination import SimplePagination
from app.extensions.source_werkingsgebieden.repository.geometry_repository import GeometryRepository


class SqliteGeometryRepository(GeometryRepository):
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
        sql = """
            INSERT INTO
                Onderverdeling
                    (
                        UUID, ID, Onderverdeling, SHAPE, symbol, Werkingsgebied, UUID_Werkingsgebied,
                        Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid
                    )
                VALUES
                    (
                        :uuid, :id, :title, GeomFromText(:shape, 28992), :symbol, :werkingsgebied, :uuid_werkingsgebied,
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
        gml: str,
        symbol: str,
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
            "gml": gml,
            "symbol": symbol,
            "created_date": created_date.strftime(DATE_FORMAT),
            "modified_date": modified_date.strftime(DATE_FORMAT),
            "start_validity": start_validity.strftime(DATE_FORMAT),
            "end_validity": end_validity.strftime(DATE_FORMAT),
        }

        sql = """
            INSERT INTO
                Werkingsgebieden
                    (
                        UUID, ID, Werkingsgebied, SHAPE, GML, symbol,
                        Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid
                    )
                VALUES
                    (
                        :uuid, :id, :title, GeomFromText(:shape, 28992), :gml, :symbol,
                        :created_date, :modified_date, :start_validity, :end_validity
                    )
            """
        self._db.execute(text(sql), params)

    def get_werkingsgebied(self, uuidx: uuid.UUID) -> dict:
        row = self.get_werkingsgebied_optional(uuidx)
        if row is None:
            raise RuntimeError(f"Werkingsgebied with UUID {uuidx} does not exist")
        return row

    def get_werkingsgebied_optional(self, uuidx: uuid.UUID) -> Optional[dict]:
        params = {
            "uuid": str(uuidx),
        }
        sql = """
            SELECT
                UUID, Werkingsgebied AS Title, symbol AS Symbol,
                Created_Date, Modified_Date, AsText(SHAPE) AS Geometry, GML,
                Begin_Geldigheid AS Start_Validity,
                Eind_Geldigheid AS End_Validity
            FROM
                Werkingsgebieden
            WHERE
                UUID = :uuid
            """
        row = self._db.execute(text(sql), params).fetchone()
        if row is None:
            return None

        row_dict = row._asdict()
        return row_dict

    def get_onderverdelingen_for_werkingsgebied(self, werkingsgebied_uuid: uuid.UUID) -> List[dict]:
        params = {
            "uuid": str(werkingsgebied_uuid),
        }
        sql = """
            SELECT
                UUID, Onderverdeling AS Title, symbol AS Symbol,
                Created_Date, Modified_Date, AsText(SHAPE) AS Geometry
            FROM
                Onderverdeling
            WHERE
                UUID_Werkingsgebied = :uuid
            """
        rows = self._db.execute(text(sql), params).all()

        dict_rows = [row._asdict() for row in rows]
        return dict_rows

    def get_werkingsgebieden_hashed(
        self,
        pagination: SimplePagination,
        title: Optional[str] = None,
        order_column: str = "Modified_Date",
        order_direction: str = "DESC",
    ) -> Tuple[int, List[Dict[str, Any]]]:
        count_sql = f"""
            SELECT COUNT(*) 
            FROM Werkingsgebieden
            { 'WHERE Werkingsgebied = :title' if title else '' }
        """
        count_params = {}
        if title:
            count_params["title"] = title

        total_count = self._db.execute(text(count_sql), count_params).scalar()

        sql = f"""
            SELECT
                UUID, ID, Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid,
                Werkingsgebied AS Title, symbol AS Symbol,
                AsText(SHAPE) AS Geometry,
                substr(hex(SHAPE), 1, 16) AS Geometry_Hash
            FROM Werkingsgebieden
            { 'WHERE Werkingsgebied = :title' if title else '' }
            ORDER BY {order_column} {order_direction}, ID
            LIMIT :limit OFFSET :offset
        """
        params = {
            "offset": pagination.offset,
            "limit": pagination.limit,
        }
        if title:
            params["title"] = title

        rows = self._db.execute(text(sql), params).all()
        dict_rows = [row._asdict() for row in rows]
        return total_count, dict_rows

    def get_werkingsgebieden_grouped_by_title(
        self, pagination: SimplePagination, order_column: str = "ID", order_direction: str = "ASC"
    ) -> Tuple[int, List[Dict[str, Any]]]:
        count_sql = """
            SELECT COUNT(DISTINCT Werkingsgebied) 
            FROM Werkingsgebieden
        """
        total_count = self._db.execute(text(count_sql)).scalar()

        sql = f"""
            WITH RankedWerkingsgebieden AS (
                SELECT
                    UUID, ID, Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid,
                    Werkingsgebied AS Title, symbol AS Symbol,
                    ROW_NUMBER() OVER (PARTITION BY Werkingsgebied ORDER BY Created_Date DESC) AS rn
                FROM Werkingsgebieden
            )
            SELECT
                UUID, ID, Created_Date, Modified_Date, Begin_Geldigheid, Eind_Geldigheid, Title, Symbol
            FROM RankedWerkingsgebieden
            WHERE rn = 1
            ORDER BY {order_column} {order_direction}
            LIMIT :limit OFFSET :offset
        """
        params = {
            "offset": pagination.offset,
            "limit": pagination.limit,
        }
        rows = self._db.execute(text(sql), params).all()
        dict_rows = [row._asdict() for row in rows]

        return total_count, dict_rows
