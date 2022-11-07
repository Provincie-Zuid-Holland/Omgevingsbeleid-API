from typing import Any, List, Generic

from sqlalchemy.orm import Query, Session, Session, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.expression import func, label, or_

from app import models, schemas
from app.crud.base import GeoCRUDBase, ModelType, CreateSchemaType, UpdateSchemaType
from app.schemas.search import GeoSearchResult
from app.util.legacy_helpers import RankedSearchObject, SearchFields


# GEO_SEARCHABLES: List[Any] = [
#     (models.Beleidskeuze, crud.beleidskeuze, schemas.Beleidskeuze),
#     (models.Maatregel, crud.maatregel, schemas.Maatregel),
#     (models.Verordening, crud.verordening, schemas.Verordening),
# ]

RANK_WEIGHT = 1
RANK_WEIGHT_HEAVY = 100


class GeoSearchService:

    def __init__(self, geo_cruds: List[GeoCRUDBase]):
        self.geo_cruds = geo_cruds

    def geo_search(
        self, uuid_list: List[str], limit: int = 10
    ) -> List[GeoSearchResult]:
        """
        Search the geo-searchable models and find all objects linked to a Werkingsgebied.

        Args:
            query (str): list of Werkingsgebied UUIDs to match

        """
        search_results = []

        # for model, service, schema in GEO_SEARCHABLES:
        for crud in self.geo_cruds:
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
