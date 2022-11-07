from datetime import datetime
from typing import List, Union

from sqlalchemy.orm import Query, joinedload
from sqlalchemy.sql import Alias

from app.crud.base import GeoCRUDBase
from app.db.base_class import NULL_UUID
from app import models, schemas
from app.schemas.filters import Filter, FilterCombiner, Filters


class CRUDMaatregel(
    GeoCRUDBase[models.Maatregel, schemas.MaatregelCreate, schemas.MaatregelUpdate]
):
    def get(self, uuid: str) -> models.Maatregel:
        return (
            self.db.query(self.model)
            .options(
                joinedload(models.Maatregel.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

    def valid_uuids(self, as_query: bool = False) -> Union[List[str], Query]:
        """
        Retrieve list of only valid UUIDs in Maatregelen
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        query = (
            self.db.query(sub_query.c.get("UUID"))
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(sub_query.c.get("Eind_Geldigheid") > datetime.utcnow())
        )
        if as_query:
            return query

        return [bk.UUID for bk in query]

    def valid_werkingsgebied_uuids(self) -> List[str]:
        """
        Retrieve list of only gebied UUIDs in valid Maatregelen
        """
        sub_query: Alias = self._build_valid_inner_query().subquery("inner")
        query = (
            self.db.query(sub_query.c.get("Gebied"))
            .filter(sub_query.c.get("RowNumber") == 1)
            .filter(sub_query.c.get("Eind_Geldigheid") > datetime.utcnow())
        )

        return [maatregel.Gebied for maatregel in query]

    # Extra status vigerend check for Maatregelen
    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query: Query = (
            self.db.query(models.Maatregel, row_number)
            .filter(models.Maatregel.Status == "Vigerend")
            .filter(models.Maatregel.UUID != NULL_UUID)
            .filter(models.Maatregel.Begin_Geldigheid <= datetime.utcnow())
        )
        return query

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> List[models.Maatregel]:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        col = models.Maatregel.Gebied_UUID
        filters = [Filter(key=col.key, value=id) for id in area_uuid]
        area_filter = Filters()
        area_filter._append_clause(combiner=FilterCombiner.OR, items=filters)

        return self.valid(filters=area_filter, limit=limit)

    def as_geo_schema(self, model: models.Maatregel):
        return schemas.Maatregel.from_orm(model)
