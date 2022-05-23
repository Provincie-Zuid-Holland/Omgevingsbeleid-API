from curses.ascii import NUL
from typing import List, Any
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import select, label, text, subquery
from sqlalchemy.sql.expression import func

from app.crud.base import CRUDBase, ModelType
from app.db.base_class import NULL_UUID
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def create(self, *, obj_in: AmbitieCreate, by_uuid: str) -> Ambitie:
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

    def latest(self, all: bool = False) -> List[ModelType]:
        partition = func.row_number().over(partition_by="ID", order_by="Modified_Date")
        row_number = label("RowNumber", partition)

        sub_query = self.db.query(self.model, row_number).subquery()
        model_alias = aliased(self.model, sub_query)

        query = (
            self.db.query(model_alias)
            .filter(sub_query.c.RowNumber == 1)
            .filter(model_alias.UUID != NULL_UUID)
        )

        if not all:
            query = query.filter(model_alias.Eind_Geldigheid > datetime.utcnow())

        # TODO filter and limit with _build_default_query
        return query.all()

ambitie = CRUDAmbitie(Ambitie)
