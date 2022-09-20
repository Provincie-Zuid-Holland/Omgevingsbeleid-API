from datetime import datetime
from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.maatregel import Maatregel
from app.schemas.filters import Filter, FilterCombiner, Filters
from app.schemas.maatregel import MaatregelCreate, MaatregelUpdate


class CRUDMaatregel(CRUDBase[Maatregel, MaatregelCreate, MaatregelUpdate]):
    def get(self, uuid: str) -> Maatregel:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Maatregel.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

    def fetch_in_geo(self, area_uuid: List[str], limit: int):
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        col = Maatregel.Gebied_UUID
        filters = [Filter(key=col.key, value=id) for id in area_uuid]
        area_filter = Filters()
        area_filter._append_clause(combiner=FilterCombiner.OR, items=filters)

        return self.valid(filters=area_filter, limit=limit)


maatregel = CRUDMaatregel(Maatregel)
