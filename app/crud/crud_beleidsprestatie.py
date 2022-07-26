from datetime import datetime

from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.beleidsprestatie import Beleidsprestatie
from app.schemas.beleidsprestatie import BeleidsprestatieCreate, BeleidsprestatieUpdate


class CRUDBeleidsprestatie(CRUDBase[Beleidsprestatie, BeleidsprestatieCreate, BeleidsprestatieUpdate]):
    def get(self, uuid: str) -> Beleidsprestatie:
        return (
            self.db.query(self.model)
            .options(
                joinedload(Beleidsprestatie.Beleidskeuzes),
            )
            .filter(self.model.UUID == uuid)
            .one()
        )

beleidsprestatie = CRUDBeleidsprestatie(Beleidsprestatie)
