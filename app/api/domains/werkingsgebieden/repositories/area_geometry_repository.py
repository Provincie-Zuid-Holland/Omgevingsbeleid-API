import uuid
from abc import ABCMeta, abstractmethod
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


# @todo: can we simplify this whole file now?
class AreaGeometryRepository(AreaRepository, metaclass=ABCMeta):
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

    def get_shape_hash(self, session: Session, idx: uuid.UUID) -> str | None:
        # TODO to SQLAlchemy
        params = {
            "id": self._format_uuid(idx),
        }
        sql = f"""
            SELECT
                {self._calculate_hex("shape")}
            FROM
                areas
            WHERE
                id = :id
            """

        row = session.execute(text(sql), params).fetchone()
        if row is None:
            return None
        return row[0]

    def create_area(
        self,
        session: Session,
        idx: uuid.UUID,
        created_date: datetime,
        created_by_id: uuid.UUID,
        onderverdeling: InputGeoOnderverdelingenTable,
    ):
        area = AreasTable(
            id=idx,
            created_date=created_date,
            created_by_id=created_by_id,
            shape=None,
            gml=onderverdeling.gml,
            source_uuid=onderverdeling.id,
            source_title=onderverdeling.title,
            source_symbol=onderverdeling.symbol,
            source_created_date=onderverdeling.created_date,
            source_geometry_index=onderverdeling.geometry_hash[0:10],
            source_geometry_hash=onderverdeling.geometry_hash,
        )
        session.add(area)
        session.flush()

        put_geometry_params = {
            "input_id": self._format_uuid(onderverdeling.id),
            "area_id": self._format_uuid(idx),
        }
        # TODO to SQLAlchemy
        # @todo: fix this
        put_geometry_stmt = """
            UPDATE
                areas
            SET
                shape = (
                    SELECT
                        geometry
                    FROM
                        input_geo_onderverdeling
                    WHERE
                        id = :input_id
                )
            WHERE
                id = :area_id
        """
        session.execute(text(put_geometry_stmt), put_geometry_params)

    def get_area(self, session: Session, idx: uuid.UUID) -> dict:
        row = self.get_area_optional(session, idx)
        if row is None:
            raise RuntimeError(f"Area with id {idx} does not exist")
        return row

    def get_area_optional(self, session: Session, idx: uuid.UUID) -> dict | None:
        # TODO to SQLAlchemy
        params = {
            "id": self._format_uuid(idx),
        }
        sql = f"""
            SELECT
                id, created_date, created_by,
                {self._shape_to_text("shape")} AS shape,
                source_title, source_symbol
            FROM
                areas
            WHERE
                id = :id
            """
        row = session.execute(text(sql), params).fetchone()
        if row is None:
            return None

        row_dict = row._asdict()
        return row_dict

    # TODO: WIP - not used yet. combine query for multiple areas for performance
    def get_areas(self, session: Session, ids: list[uuid.UUID]) -> dict[uuid.UUID, dict]:
        placeholders = ", ".join(f":uuid{i}" for i in range(len(ids)))
        params = {f"id{i}": idx for i, idx in enumerate(ids)}
        # TODO to SQLAlchemy
        sql = f"""
            SELECT
                id, created_date, created_by,
                {self._shape_to_text("shape")} AS shape,
                source_title, source_symbol
            FROM
                areas
            WHERE
                id IN ({placeholders})
            """
        rows = session.execute(text(sql), params).fetchall()
        return {row.UUID: row._asdict() for row in rows}
