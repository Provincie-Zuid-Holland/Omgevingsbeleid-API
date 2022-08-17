from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.gebiedsprogramma import Gebiedsprogramma
from app.schemas.gebiedsprogramma import GebiedsprogrammaCreate, GebiedsprogrammaUpdate


class CRUDGebiedsprogramma(
    CRUDBase[Gebiedsprogramma, GebiedsprogrammaCreate, GebiedsprogrammaUpdate]
):
    def get(self, uuid: str) -> Gebiedsprogramma:
        return (
            self.db.query(self.model)
            .options(joinedload(Gebiedsprogramma.Maatregelen))
            .filter(self.model.UUID == uuid)
            .one()
        )


gebiedsprogramma = CRUDGebiedsprogramma(Gebiedsprogramma)
