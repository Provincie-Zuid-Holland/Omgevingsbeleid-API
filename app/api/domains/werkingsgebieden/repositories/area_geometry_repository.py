import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from shapely import wkt
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.repositories.area_repository import (
    VALID_GEOMETRIES,
    AreaRepository,
    GeometryFunctions,
)
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingTable


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
    def get_spatial_function(self, func: GeometryFunctions) -> str:
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

    def get_area_uuids_by_geometry(
        self, session: Session, geometry: str, geometry_func: GeometryFunctions
    ) -> List[uuid.UUID]:
        # Validating the geometry should have been done already
        # But I do it again here because we insert it as plain text into sql.
        # Better be safe
        try:
            geom = wkt.loads(geometry)
            if geom.geom_type not in VALID_GEOMETRIES:
                raise RuntimeError("Geometry is not a valid shape")
        except Exception:
            raise RuntimeError("Geometry is not a valid shape")

        spatial_function = self.get_spatial_function(geometry_func)
        text_to_shape_func = self._text_to_shape("polygon")
        geometry_filter = f"Shape.{spatial_function}({text_to_shape_func}) = 1"

        areas_stmt = (
            select(AreasTable.UUID)
            .select_from(AreasTable)
            .filter(text(geometry_filter))
            .params(
                polygon=geometry,
            )
        )
        rows = session.execute(areas_stmt).fetchall()

        return [row.UUID for row in rows]

    def create_area(
        self,
        session: Session,
        uuidx: uuid.UUID,
        created_date: datetime,
        created_by_uuid: uuid.UUID,
        onderverdeling: InputGeoOnderverdelingTable,
    ):
        area = AreasTable(
            UUID=uuidx,
            Created_Date=created_date,
            Created_By_UUID=created_by_uuid,
            Shape=None,
            Gml=onderverdeling.GML,
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
