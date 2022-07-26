from datetime import datetime

from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.verordening import Verordening
from app.schemas.verordening import VerordeningCreate, VerordeningUpdate


class CRUDVerordening(CRUDBase[Verordening, VerordeningCreate, VerordeningUpdate]):
    def get(self, uuid: str) -> Verordening:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Verordening.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

verordening = CRUDVerordening(Verordening)
