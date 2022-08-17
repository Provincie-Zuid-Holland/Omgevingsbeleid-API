from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.werkingsgebied import Werkingsgebied
from app.schemas.werkingsgebied import WerkingsgebiedCreate, WerkingsgebiedUpdate


class CRUDWerkingsgebied(
    CRUDBase[Werkingsgebied, WerkingsgebiedCreate, WerkingsgebiedUpdate]
):
    def get(self, uuid: str) -> Werkingsgebied:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Werkingsgebied.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )


werkingsgebied = CRUDWerkingsgebied(Werkingsgebied)
