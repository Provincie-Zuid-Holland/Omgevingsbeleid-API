import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import GeometryFunctions
from app.core.tables.others import AreasTable

POSTGRESQL_SPATIAL_FUNCTION_MAP = {
    GeometryFunctions.CONTAINS: "ST_Contains",
    GeometryFunctions.WITHIN: "ST_Within",
    GeometryFunctions.OVERLAPS: "ST_Overlaps",
    GeometryFunctions.INTERSECTS: "ST_Intersects",
}


class PostgresqlAreaGeometryRepository(AreaGeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"ST_GeomFromText(:{key}, 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"ST_AsText({column})"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return str(uuidx)

    def get_spatial_function(self, func: GeometryFunctions) -> str:
        return POSTGRESQL_SPATIAL_FUNCTION_MAP[func]

    def _calculate_hex(self, column: str) -> str:
        return f"encode(ST_AsEWKB({column}), 'hex')"

    def get_shape_hash(self, session: Session, uuidx: uuid.UUID) -> Optional[str]:
        stmt = (
            select(
                func.encode(
                    func.ST_AsEWKB(AreasTable.Shape),
                    "hex",
                )
            )
            .where(AreasTable.UUID == uuidx)
        )
        result = session.execute(stmt).scalar_one_or_none()
        return result
