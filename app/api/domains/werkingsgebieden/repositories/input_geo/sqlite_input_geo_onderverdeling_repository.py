import uuid


from app.api.domains.werkingsgebieden.repositories.input_geo.input_geo_onderverdeling_repository import InputGeoOnderverdelingRepository


class SqliteInputGeoOnderverdelingRepository(InputGeoOnderverdelingRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"GeomFromText(:{key}, 28992)"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return uuidx.hex
