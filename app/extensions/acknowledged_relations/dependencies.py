from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.acknowledged_relations.repository.acknowledged_relations_repository import (
    AcknowledgedRelationsRepository,
)


def depends_acknowledged_relations_repository(
    db: Session = Depends(depends_db),
) -> AcknowledgedRelationsRepository:
    return AcknowledgedRelationsRepository(db)
