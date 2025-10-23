import uuid

from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import GeometryFunctions

MSSQL_SPATIAL_FUNCTION_MAP = {
    GeometryFunctions.CONTAINS: "STContains",
    GeometryFunctions.WITHIN: "STWithin",
    GeometryFunctions.OVERLAPS: "STOverlaps",
    GeometryFunctions.INTERSECTS: "STIntersects",
}


class MssqlAreaGeometryRepository(AreaGeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"geometry::STGeomFromText(CONVERT(nvarchar(max), :{key}), 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"{column}.STAsText()"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return str(uuidx)

    def get_spatial_function(self, func: GeometryFunctions) -> str:
        return MSSQL_SPATIAL_FUNCTION_MAP[func]

    def _calculate_hex(self, column: str) -> str:
        return f"CONVERT(varchar(max), {column}.STAsBinary(), 2)"
