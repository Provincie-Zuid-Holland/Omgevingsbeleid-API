import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.core.utils.utils import DATE_FORMAT
from app.dynamic.utils.pagination import PaginatedQueryResult, SimplePagination, SortedPagination
from app.extensions.source_werkingsgebieden.repository.geometry_repository import GeometryRepository


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
        sql = """
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
            "created_date": created_date.strftime(DATE_FORMAT)[:23],
            "modified_date": modified_date.strftime(DATE_FORMAT)[:23],
            "start_validity": start_validity.strftime(DATE_FORMAT)[:23],
            "end_validity": end_validity.strftime(DATE_FORMAT)[:23],
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
                        :uuid, :id, :title, geometry::STGeomFromText(:shape, 28992), :gml, :symbol,
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
                Created_Date, Modified_Date, SHAPE.STAsText() AS Geometry, GML,
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
                Created_Date, Modified_Date, SHAPE.STAsText() AS Geometry
            FROM
                Onderverdeling
            WHERE
                UUID_Werkingsgebied = :uuid
            """
        rows = self._db.execute(text(sql), params).all()

        dict_rows = [row._asdict() for row in rows]
        return dict_rows

    def get_werkingsgebieden_hashed(self, pagination: SimplePagination, title: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        count_sql = f"""
            SELECT COUNT(*) 
            FROM Werkingsgebieden
            { 'WHERE "Werkingsgebieden"."Werkingsgebied" = :title' if title else '' }
        """
        count_params = {}
        if title:
            count_params["title"] = title

        total_count = self._db.execute(text(count_sql), count_params).scalar()

        sql = f"""
            SELECT
                "Werkingsgebieden"."UUID",
                "Werkingsgebieden"."ID",
                "Werkingsgebieden"."Created_Date",
                "Werkingsgebieden"."Modified_Date",
                "Werkingsgebieden"."Begin_Geldigheid",
                "Werkingsgebieden"."Eind_Geldigheid",
                "Werkingsgebieden"."Werkingsgebied" AS Title,
                "Werkingsgebieden".symbol AS Symbol,
                "Werkingsgebieden"."SHAPE".STAsText() AS Geometry,
                LEFT(CONVERT(VARCHAR(MAX), HASHBYTES('SHA2_256', "Werkingsgebieden"."SHAPE".STAsBinary()), 2), 16) AS "Geometry_Hash"
            FROM Werkingsgebieden
            { 'WHERE "Werkingsgebieden"."Werkingsgebied" = :title' if title else '' }
            ORDER BY "Werkingsgebieden"."ID"
            OFFSET :offset ROWS
            FETCH NEXT :limit ROWS ONLY
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

    def get_werkingsgebieden_grouped_by_title(self, pagination: SimplePagination) -> Tuple[int, List[Dict[str, Any]]]:
        count_sql = """
            SELECT COUNT(DISTINCT "Werkingsgebieden"."Werkingsgebied") 
            FROM Werkingsgebieden
        """
        total_count = self._db.execute(text(count_sql)).scalar()

        sql = f"""
            WITH RankedWerkingsgebieden AS (
                SELECT
                    "Werkingsgebieden"."UUID",
                    "Werkingsgebieden"."ID",
                    "Werkingsgebieden"."Created_Date",
                    "Werkingsgebieden"."Modified_Date",
                    "Werkingsgebieden"."Begin_Geldigheid",
                    "Werkingsgebieden"."Eind_Geldigheid",
                    "Werkingsgebieden"."Werkingsgebied" AS Title,
                    "Werkingsgebieden".symbol AS Symbol,
                    "Werkingsgebieden"."SHAPE".STAsText() AS Geometry,
                    ROW_NUMBER() OVER (PARTITION BY "Werkingsgebieden"."Werkingsgebied" ORDER BY "Werkingsgebieden"."Created_Date" DESC) AS rn
                FROM Werkingsgebieden
            )
            SELECT
                UUID,
                ID,
                Created_Date,
                Modified_Date,
                Begin_Geldigheid,
                Eind_Geldigheid,
                Title,
                Symbol,
                Geometry
            FROM RankedWerkingsgebieden
            WHERE rn = 1  -- Get the first (newest) entry per group
            ORDER BY ID
            OFFSET :offset ROWS
            FETCH NEXT :limit ROWS ONLY
        """
        params = {
            "offset": pagination.offset,
            "limit": pagination.limit,
        }
        rows = self._db.execute(text(sql), params).all()
        dict_rows = [row._asdict() for row in rows]

        return total_count, dict_rows