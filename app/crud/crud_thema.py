from datetime import datetime

from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.thema import Thema
from app.schemas.thema import ThemaUpdate, ThemaCreate


class CRUDThema(CRUDBase[Thema, ThemaCreate, ThemaUpdate]):
    def get(self, uuid: str) -> Thema:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Thema.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

thema = CRUDThema(Thema)
