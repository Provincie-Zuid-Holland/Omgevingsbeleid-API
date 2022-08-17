
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.beleidsregel import Beleidsregel
from app.schemas.beleidsregel import BeleidsregelCreate, BeleidsregelUpdate


class CRUDBeleidsregel(CRUDBase[Beleidsregel, BeleidsregelCreate, BeleidsregelUpdate]):
    def get(self, uuid: str) -> Beleidsregel:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Beleidsregel.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )


beleidsregel = CRUDBeleidsregel(Beleidsregel)
