import uuid

from app.extensions.areas.models.models import GeometryFunctions

from . import AreaGeometryRepository

SQLITE_SPATIAL_FUNCTION_MAP = {
    GeometryFunctions.CONTAINS: "ST_Contains",
    GeometryFunctions.WITHIN: "ST_Within",
    GeometryFunctions.OVERLAPS: "ST_Overlaps",
    GeometryFunctions.INTERSECTS: "ST_Intersects",
}


class SqliteAreaGeometryRepository(AreaGeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"GeomFromText(:{key}, 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"AsText({column})"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return uuidx.hex

    def get_spatial_function(self, func: GeometryFunctions) -> str:
        return SQLITE_SPATIAL_FUNCTION_MAP[func]
