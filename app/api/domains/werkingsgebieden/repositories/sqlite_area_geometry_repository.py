import uuid

from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository


class SqliteAreaGeometryRepository(AreaGeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"GeomFromText(:{key}, 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"AsText({column})"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return uuidx.hex

    def _calculate_hex(self, column: str) -> str:
        return f"hex({column})"
