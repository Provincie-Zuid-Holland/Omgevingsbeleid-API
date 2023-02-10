
from app.crud.base import CRUDBase
from app.models.beleidsdoel import Beleidsdoel
from app.schemas.beleidsdoel import BeleidsdoelCreate, BeleidsdoelUpdate


class CRUDBeleidsdoel(CRUDBase[Beleidsdoel, BeleidsdoelCreate, BeleidsdoelUpdate]):
    def get(self, uuid: str) -> Beleidsdoel:
        return self.db.query(self.model).filter(self.model.UUID == uuid).one()


crud_beleidsdoel = CRUDBeleidsdoel(model=Beleidsdoel)
