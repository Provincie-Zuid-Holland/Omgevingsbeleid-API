from sqlalchemy.orm import Query

from app.crud.base import CRUDBase
from app.models.ambitie import Ambitie
from app.schemas.ambitie import AmbitieCreate, AmbitieUpdate


class CRUDAmbitie(CRUDBase[Ambitie, AmbitieCreate, AmbitieUpdate]):
    def get(self, uuid: str) -> Ambitie:
        query = (
            Query(Ambitie)
            .filter(Ambitie.UUID == uuid)
        )

        query.session = self.db
        return query.one()
