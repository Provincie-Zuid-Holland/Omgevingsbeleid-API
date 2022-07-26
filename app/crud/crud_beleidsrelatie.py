from app.crud.base import CRUDBase
from app.models.beleidsrelatie import Beleidsrelatie
from app.schemas.beleidsrelatie import BeleidsrelatieCreate, BeleidsrelatieUpdate

class CRUDBeleidsrelatie(CRUDBase[Beleidsrelatie, BeleidsrelatieCreate, BeleidsrelatieUpdate]):
    pass

beleidsrelatie = CRUDBeleidsrelatie(Beleidsrelatie)
