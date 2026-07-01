import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


class AreaGeometryRepository(AreaRepository, metaclass=ABCMeta):
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

    def get_shape_hash(self, session: Session, uuidx: uuid.UUID) -> Optional[str]:
        params = {
            "uuid": self._format_uuid(uuidx),
        }
        sql = f"""
            SELECT
                {self._calculate_hex("Shape")}
            FROM
                areas
            WHERE
                UUID = :uuid
            """

        row = session.execute(text(sql), params).fetchone()
        if row is None:
            return None
        return row[0]

    def create_area(
        self,
        session: Session,
        uuidx: uuid.UUID,
        created_date: datetime,
        created_by_uuid: uuid.UUID,
        onderverdeling: InputGeoOnderverdelingenTable,
    ):
        area = AreasTable(
            UUID=uuidx,
            Created_Date=created_date,
            Created_By_UUID=created_by_uuid,
            Shape=None,
            Gml=onderverdeling.GML,
            Source_Symbol=onderverdeling.Symbol,
            Source_Geometry_Index=onderverdeling.Geometry_Hash[0:10],
            Source_Geometry_Hash=onderverdeling.Geometry_Hash,
            Source_UUID=onderverdeling.UUID,
            Source_Title=onderverdeling.Title,
            Source_Created_Date=onderverdeling.Created_Date,
        )
        session.add(area)
        session.flush()

        put_geometry_params = {
            "input_uuid": self._format_uuid(onderverdeling.UUID),
            "area_uuid": self._format_uuid(uuidx),
        }
        put_geometry_stmt = """
            UPDATE
                areas
            SET
                Shape = (
                    SELECT
                        Geometry
                    FROM
                        Input_GEO_Onderverdeling
                    WHERE
                        UUID = :input_uuid
                )
            WHERE
                UUID = :area_uuid
        """
        session.execute(text(put_geometry_stmt), put_geometry_params)

    def get_area(self, session: Session, uuidx: uuid.UUID) -> dict:
        row = self.get_area_optional(session, uuidx)
        if row is None:
            raise RuntimeError(f"Area with UUID {uuidx} does not exist")
        return row

    def get_area_optional(self, session: Session, uuidx: uuid.UUID) -> Optional[dict]:
        params = {
            "uuid": self._format_uuid(uuidx),
        }
        sql = f"""
            SELECT
                UUID, Created_Date, Created_By_UUID,
                {self._shape_to_text("Shape")} AS Shape,
                Source_Title, Source_Symbol
            FROM
                areas
            WHERE
                UUID = :uuid
            """
        row = session.execute(text(sql), params).fetchone()
        if row is None:
            return None

        row_dict = row._asdict()
        return row_dict

    # TODO: WIP - not used yet. combine query for multiple areas for performance
    def get_areas(self, session: Session, uuids: List[uuid.UUID]) -> Dict[uuid.UUID, dict]:
        placeholders = ", ".join(f":uuid{i}" for i in range(len(uuids)))
        params = {f"uuid{i}": uuid for i, uuid in enumerate(uuids)}
        sql = f"""
            SELECT
                UUID, Created_Date, Created_By_UUID,
                {self._shape_to_text("Shape")} AS Shape,
                Source_Title, Source_Symbol
            FROM
                areas
            WHERE
                UUID IN ({placeholders})
            """
        rows = session.execute(text(sql), params).fetchall()
        return {row.UUID: row._asdict() for row in rows}
