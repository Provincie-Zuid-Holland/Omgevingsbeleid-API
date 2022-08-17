
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.maatregel import Maatregel
from app.schemas.maatregel import MaatregelCreate, MaatregelUpdate


class CRUDMaatregel(CRUDBase[Maatregel, MaatregelCreate, MaatregelUpdate]):
    def get(self, uuid: str) -> Maatregel:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Maatregel.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )


maatregel = CRUDMaatregel(Maatregel)
