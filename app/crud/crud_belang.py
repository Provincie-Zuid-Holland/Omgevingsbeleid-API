from app.crud.base import CRUDBase
from app.models.belang import Belang
from app.schemas.belang import BelangCreate, BelangUpdate


class CRUDBelang(CRUDBase[Belang, BelangCreate, BelangUpdate]):
    pass
