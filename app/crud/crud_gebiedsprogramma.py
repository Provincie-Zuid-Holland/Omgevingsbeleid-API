from datetime import datetime
from sqlalchemy.orm import Query
from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.models.base import Status
from app.models.gebiedsprogrammas import Gebiedsprogramma
from app.schemas.gebiedsprogramma import GebiedsprogrammaCreate, GebiedsprogrammaUpdate


class CRUDGebiedsprogramma(
    CRUDBase[Gebiedsprogramma, GebiedsprogrammaCreate, GebiedsprogrammaUpdate]
):

    # Extra status vigerend check
    def _build_valid_inner_query(self) -> Query:
        """
        Base valid query usable as subquery
        """
        row_number = self._add_rownumber_latest_id()
        query = (
            Query([Gebiedsprogramma, row_number])
            .filter(Gebiedsprogramma.Status == Status.VIGEREND.value)
            .filter(Gebiedsprogramma.UUID != NULL_UUID)
            .filter(Gebiedsprogramma.Begin_Geldigheid <= datetime.utcnow())
        )
        return query
