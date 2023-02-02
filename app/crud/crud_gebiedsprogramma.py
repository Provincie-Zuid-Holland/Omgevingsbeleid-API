from datetime import datetime
from typing import Type

from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session

from app.crud.base import CRUDBase
from app.db.base_class import NULL_UUID
from app.db.session import SessionLocal
from app.models.base import Status
from app.models.gebiedsprogrammas import Gebiedsprogramma
from app.schemas.gebiedsprogramma import GebiedsprogrammaCreate, GebiedsprogrammaUpdate


class CRUDGebiedsprogramma(
    CRUDBase[Gebiedsprogramma, GebiedsprogrammaCreate, GebiedsprogrammaUpdate]
):
    def __init__(
        self,
        db: Session = SessionLocal(),
        model: Type[Gebiedsprogramma] = Gebiedsprogramma,
    ):
        super().__init__(model=model, db=db)

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
