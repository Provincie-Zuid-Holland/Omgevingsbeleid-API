from curses.ascii import NUL
from typing import List, Any
from datetime import datetime

from fastapi.encoders import jsonable_encoder

from app.crud.base import CRUDBase, ModelType
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


beleidskeuze = CRUDBeleidskeuze(Beleidskeuze)
