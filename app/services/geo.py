from typing import List


from app import schemas
from app.crud.base import GeoCRUDBase
from app.schemas.search import GeoSearchResult


RANK_WEIGHT = 1
RANK_WEIGHT_HEAVY = 100


class GeoSearchService:
    def __init__(self, geo_cruds: List[GeoCRUDBase]):
        self.search_entities = geo_cruds

    def geo_search(
        self, uuid_list: List[str], limit: int = 10
    ) -> List[GeoSearchResult]:
        """
        Search the geo-searchable models and find all objects linked to a Werkingsgebied.

        Args:
            query (str): list of Werkingsgebied UUIDs to match

        """
        search_results = []

        for crud in self.search_entities:
            if len(search_results) >= limit:
                return search_results

            search_hits = crud.fetch_in_geo(uuid_list, limit)

            for item in search_hits:
                pyd_object = crud.as_geo_schema(item)
                search_fields = crud.model.get_search_fields()
                area_value = getattr(item, "Gebied")

                if type(area_value) is not str:
                    area_value = area_value.UUID

                search_results.append(
                    schemas.GeoSearchResult(
                        Gebied=area_value,
                        Titel=getattr(pyd_object, search_fields.title.key),
                        Omschrijving=getattr(
                            pyd_object, search_fields.description[0].key
                        ),
                        Type=item.__tablename__,
                        UUID=pyd_object.UUID,
                    )
                )

        return search_results
