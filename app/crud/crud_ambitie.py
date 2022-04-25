from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def create(
        self, db: Session, *, obj_in: AmbitieCreate, by_uuid: str
    ) -> Ambitie:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, created_by=by_uuid)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, by_uuid: str, skip: int = 0, limit: int = 100
    ) -> List[Ambitie]:
        return (
            db.query(self.model)
            .filter(Ambitie.Created_by == by_uuid)
            .offset(skip)
            .limit(limit)
            .all()
        )


ambitie = CRUDAmbitie(Ambitie)
