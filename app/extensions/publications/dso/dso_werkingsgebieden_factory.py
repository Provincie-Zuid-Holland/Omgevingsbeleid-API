from typing import List, Set
from uuid import UUID

from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.werkingsgebieden.repository.geometry_repository import GeometryRepository


class DsoWerkingsgebiedenFactory:
    def __init__(self, geometry_repository: GeometryRepository):
        self._geometry_repository: GeometryRepository = geometry_repository

    def get_repository_for_objects(self, objects: List[dict]) -> WerkingsgebiedRepository:
        uuidx: List[UUID] = self._calculate_werkingsgebieden_uuids(objects)
        repository: WerkingsgebiedRepository = self._create_repository(uuidx)
        return repository

    def _create_repository(self, uuids: List[UUID]) -> WerkingsgebiedRepository:
        repository = WerkingsgebiedRepository("pv28", "nld")
        for uuidx in uuids:
            werkingsgebied = self._get_werkingsgebied(uuidx)
            repository.add(werkingsgebied)
        return repository

    def _get_werkingsgebied(self, werkingsgebied_uuid: UUID) -> dict:
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

    def _calculate_werkingsgebieden_uuids(self, objects: List[dict]) -> List[UUID]:
        uuids: Set[UUID] = set([o.get("Gebied_UUID") for o in objects if o.get("Gebied_UUID", None) is not None])
        return list(uuids)
