from typing import List, Optional
import uuid

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from app.extensions.regulations.db.tables import RegulationsTable


class RegulationsRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_all(self) -> List[RegulationsTable]:
        stmt = select(RegulationsTable).order_by(asc(RegulationsTable.Title))

        rows: List[RegulationsTable] = self._db.scalars(stmt).all()
        return rows

    def get_by_uuid(self, regulation_uuid: uuid.UUID) -> Optional[RegulationsTable]:
        stmt = select(RegulationsTable).where(RegulationsTable.UUID == regulation_uuid)
        maybe_regulation: Optional[RegulationsTable] = self._db.scalars(stmt).first()

        return maybe_regulation
