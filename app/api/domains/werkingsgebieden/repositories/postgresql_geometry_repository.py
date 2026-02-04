import uuid


from app.api.domains.werkingsgebieden.repositories.geometry_repository import GeometryRepository


class PostgresqlGeometryRepository(GeometryRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"ST_GeomFromText(:{key}, 28992)"

    def _shape_to_text(self, column: str) -> str:
        return f"ST_AsText({column})"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return str(uuidx)

    def _calculate_hex(self, column: str) -> str:
        return f"encode(ST_AsEWKB({column}), 'hex')"
