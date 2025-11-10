import uuid


from app.api.domains.werkingsgebieden.repositories.geometry_repository import GeometryRepository


class SqliteGeometryRepository(GeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"GeomFromText(:{key}, 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"AsText({column})"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return uuidx.hex

    def _calculate_hex(self, column: str) -> str:
        return f"hex({column})"
