from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.beleidsmodule import Beleidsmodule
from app.schemas.beleidsmodule import BeleidsmoduleCreate, BeleidsmoduleUpdate


class CRUDBeleidsmodule(CRUDBase[Beleidsmodule, BeleidsmoduleCreate, BeleidsmoduleUpdate]):
    def get(self, uuid: str) -> Beleidsmodule:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Beleidsmodule.Beleidskeuzes),
                joinedload(Beleidsmodule.Maatregelen),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

beleidsmodule = CRUDBeleidsmodule(Beleidsmodule)
