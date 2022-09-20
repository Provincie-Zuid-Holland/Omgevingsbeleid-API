from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def get(self, uuid: str) -> Ambitie:
        return (
            self.db.query(self.model)
            .options(joinedload(Ambitie.Beleidskeuzes))
            .filter(self.model.UUID == uuid)
            .one()
        )


ambitie = CRUDAmbitie(Ambitie)
