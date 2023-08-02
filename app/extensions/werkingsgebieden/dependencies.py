from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.werkingsgebieden.repository import WerkingsgebiedenRepository


def depends_werkingsgebieden_repository(
    db: Session = Depends(depends_db),
) -> WerkingsgebiedenRepository:
    return WerkingsgebiedenRepository(db)
