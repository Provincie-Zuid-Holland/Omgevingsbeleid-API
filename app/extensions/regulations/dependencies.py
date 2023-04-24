from typing import Optional
from fastapi import Depends, HTTPException
import uuid

from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.extensions.regulations.db.tables import RegulationsTable
from app.extensions.regulations.repository.regulations_repository import (
    RegulationsRepository,
)


def depends_regulations_repository(
    db: Session = Depends(depends_db),
) -> RegulationsRepository:
    return RegulationsRepository(db)


def depends_regulation(
    regulation_uuid: uuid.UUID,
    repository: RegulationsRepository = Depends(depends_regulations_repository),
) -> RegulationsTable:
    maybe_regulation: Optional[RegulationsTable] = repository.get_by_uuid(
        regulation_uuid
    )
    if not maybe_regulation:
        raise HTTPException(status_code=404, detail="Regulation niet gevonden")
    return maybe_regulation
