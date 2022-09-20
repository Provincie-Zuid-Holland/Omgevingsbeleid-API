from datetime import datetime
from typing import Any, List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import or_
from app import models

from app.crud.base import CRUDBase
from app.models.beleidskeuze import Beleidskeuze
from app.schemas.beleidskeuze import BeleidskeuzeCreate, BeleidskeuzeUpdate


class CRUDBeleidskeuze(CRUDBase[Beleidskeuze, BeleidskeuzeCreate, BeleidskeuzeUpdate]):
    def create(self, *, obj_in: BeleidskeuzeCreate, by_uuid: str) -> Beleidskeuze:
        obj_in_data = jsonable_encoder(
            obj_in,
            custom_encoder={
                datetime: lambda dt: dt,
            },
        )

        request_time = datetime.now()

        obj_in_data["Created_By_UUID"] = by_uuid
        obj_in_data["Modified_By_UUID"] = by_uuid
        obj_in_data["Created_Date"] = request_time
        obj_in_data["Modified_Date"] = request_time

        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def fetch_in_geo(self, area_uuid: List[str], limit: int) -> Any:
        """
        Retrieve the instances of this entity linked
        to the IDs of provided geological areas.
        """
        association = models.Beleidskeuze_Werkingsgebieden
        filter_list = [(association.Werkingsgebied_UUID == uuid) for uuid in area_uuid]
        
        # Query using the geo UUID in assoc table
        result = (
            self.db.query(association)
            .options(joinedload(association.Beleidskeuze))
            .filter(or_(*filter_list))
            .limit(limit)
            .all()
        )

        if result is None:
            return []

        def beleidskeuze_mapper(association_object: association):
            # return beleidskeuzes but keep Gebied field
            # to return in GeoSearchResult response
            mapped = association_object.Beleidskeuze 
            setattr(mapped, 'Gebied', association_object.Werkingsgebied_UUID)
            return mapped

        return list(map(beleidskeuze_mapper, result))


beleidskeuze = CRUDBeleidskeuze(Beleidskeuze)
