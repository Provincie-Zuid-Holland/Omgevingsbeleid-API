from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase, ModelType
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    # def create(self, *, obj_in: AmbitieCreate, by_uuid: str) -> Ambitie:
        # obj_in_data = jsonable_encoder(
            # obj_in,
            # custom_encoder={
                # datetime: lambda dt: dt,
            # },
        # )
# 
        # request_time = datetime.now()
# 
        # obj_in_data["Created_By_UUID"] = by_uuid
        # obj_in_data["Modified_By_UUID"] = by_uuid
        # obj_in_data["Created_Date"] = request_time
        # obj_in_data["Modified_Date"] = request_time
# 
        # db_obj = self.model(**obj_in_data)
        # self.db.add(db_obj)
        # self.db.commit()
        # self.db.refresh(db_obj)
        # return db_obj

    def get(self, uuid: str) -> ModelType:
        return (
            self.db.query(self.model)
            .options(joinedload(Ambitie.Beleidskeuzes))
            .filter(self.model.UUID == uuid)
            .one()
        )


ambitie = CRUDAmbitie(Ambitie)
