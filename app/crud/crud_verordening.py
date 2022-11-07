from datetime import datetime
from typing import List

from sqlalchemy.orm import joinedload

from app.crud.base import GeoCRUDBase
from app.schemas.filters import Filter, FilterCombiner, Filters
from app import models, schemas


class CRUDVerordening(GeoCRUDBase[models.Verordening, schemas.VerordeningCreate, schemas.VerordeningUpdate]):
    def get(self, uuid: str) -> models.Verordening:
        return (
            self.db.query(models.Verordening)
            .options(
                joinedload(models.Verordening.Beleidskeuzes),
            )
            .filter(models.Verordening.UUID == uuid)
            .one()
        )

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> List[models.Verordening]:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        col = models.Verordening.Gebied_UUID
        area_filter = Filters()
        filters = [Filter(key=col.key, value=id) for id in area_uuid]
        area_filter._append_clause(combiner=FilterCombiner.OR, items=filters)

        return self.valid(filters=area_filter, limit=limit)

    def as_geo_schema(self, model: models.Verordening):
        return schemas.Verordening.from_orm(model)

    def valid_without_lid_type(self):
        """
        Retrieve valid Verordeningen filered
        to exclude 'Lid' type records
        """
        type_filter = Filters()
        filter = Filter(key=models.Verordening.Type.key, value="Lid", negation=True)
        type_filter._append_clause(combiner=FilterCombiner.OR, items=[filter])

        return self.valid(filters=type_filter, limit=-1)

    # Overwrite base valid filter
    def fetch_graph_nodes(self):
        return self.valid_without_lid_type()
