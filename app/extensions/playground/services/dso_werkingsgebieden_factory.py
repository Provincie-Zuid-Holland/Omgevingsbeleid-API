from uuid import UUID

from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository


class DsoWerkingsgebiedenFactory:
    def __init__(self, geometry_repository: GeometryRepository):
        self._geometry_repository: GeometryRepository = geometry_repository

    def get(self, werkingsgebied_uuid: UUID) -> dict:
        werkingsgebied = self._geometry_repository.get_werkingsgebied(werkingsgebied_uuid)
        onderverdelingen = self._geometry_repository.get_onderverdelingen_for_werkingsgebied(werkingsgebied_uuid)

        if len(onderverdelingen) == 0:
            # If we do not have an Onderverdeling
            # Then we transform the Werkingsgebied as its own Onderverdeling
            onderverdelingen.append(
                {
                    "UUID": werkingsgebied["UUID"],
                    "Title": werkingsgebied["Title"],
                    "Symbol": werkingsgebied["Symbol"],
                    "Geometry": werkingsgebied["Geometry"],
                    "Created_Date": werkingsgebied["Created_Date"],
                    "Modified_Date": werkingsgebied["Modified_Date"],
                }
            )

        result = {
            "UUID": werkingsgebied["UUID"],
            "Title": werkingsgebied["Title"],
            "Symbol": werkingsgebied["Symbol"],
            "Created_Date": werkingsgebied["Created_Date"],
            "Modified_Date": werkingsgebied["Modified_Date"],
            "Achtergrond_Verwijzing": "TOP10NL",
            "Achtergrond_Actualiteit": werkingsgebied["Modified_Date"][:10],
            "Onderverdelingen": onderverdelingen,
        }
        return result
