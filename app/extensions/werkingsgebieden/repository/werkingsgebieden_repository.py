from typing import List

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable


class WerkingsgebiedenRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_all(self) -> List[WerkingsgebiedenTable]:
        stmt = select(WerkingsgebiedenTable).order_by(
            desc(WerkingsgebiedenTable.Modified_Date)
        )

        rows: List[WerkingsgebiedenTable] = self._db.scalars(stmt).all()
        return rows
