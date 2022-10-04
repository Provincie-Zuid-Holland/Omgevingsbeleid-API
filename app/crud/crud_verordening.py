from datetime import datetime
from typing import List

from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.verordening import Verordening
from app.schemas.filters import Filter, FilterCombiner, Filters
from app.schemas.verordening import VerordeningCreate, VerordeningUpdate


class CRUDVerordening(CRUDBase[Verordening, VerordeningCreate, VerordeningUpdate]):
    def get(self, uuid: str) -> Verordening:
        return (
            self.db.query(Verordening)
            .options(
                joinedload(Verordening.Beleidskeuzes),
            )
            .filter(Verordening.UUID == uuid)
            .one()
        )

    def fetch_in_geo(self, area_uuid: List[str], limit: int):
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        col = Verordening.Gebied_UUID
        area_filter = Filters()
        filters = [Filter(key=col.key, value=id) for id in area_uuid]
        area_filter._append_clause(combiner=FilterCombiner.OR, items=filters)

        return self.valid(filters=area_filter, limit=limit)

    def valid_without_lid_type(self):
        """
        Retrieve valid Verordeningen filered
        to exclude 'Lid' type records
        """
        type_filter = Filters()
        filter = Filter(key=Verordening.Type.key, value="Lid", negation=True)
        type_filter._append_clause(combiner=FilterCombiner.OR, items=[filter])

        return self.valid(filters=type_filter, limit=-1)

    # Overwrite base valid filter
    def fetch_graph_nodes(self):
        return self.valid_without_lid_type()


verordening = CRUDVerordening(Verordening)
