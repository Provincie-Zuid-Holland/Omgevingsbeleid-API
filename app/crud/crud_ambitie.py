from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def create(
        self, db: Session, *, obj_in: AmbitieCreate, by_uuid: str
    ) -> Ambitie:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, Created_By=by_uuid)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 20
    ) -> List[Ambitie]:
        return (
            db.query(self.model)
            # .options(joinedload(self.model.Created_By))
            .order_by(self.model.Modified_Date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


ambitie = CRUDAmbitie(Ambitie)
