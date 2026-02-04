import uuid


from app.api.domains.werkingsgebieden.repositories.input_geo.input_geo_onderverdeling_repository import (
    InputGeoOnderverdelingRepository,
)


class MssqlInputGeoOnderverdelingRepository(InputGeoOnderverdelingRepository):
    def _text_to_shape(self, key: str) -> str:
        return f"geometry::STGeomFromText(:{key}, 28992)"

    def _format_uuid(self, uuidx: uuid.UUID) -> str:
        return str(uuidx)
